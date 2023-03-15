import numpy as np
import re
from transforms3d.euler import euler2mat, mat2euler


class BvhJoint:
    def __init__(self, name, parent):
        self.index = []
        self.name = name
        self.parent = parent
        self.offset = np.zeros(3)
        self.channels = []
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):
        return self.name

    def position_animated(self):
        return any([x.endswith('position') for x in self.channels])

    def rotation_animated(self):
        return any([x.endswith('rotation') for x in self.channels])


class Bvh:
    def __init__(self):
        self.joints = {}
        self.root = None
        self.keyframes = None
        self.filename = ""
        self.frames = 0
        self.fps = 0
        self.positions = {}
        self.rotations = {}
        self.node_and_parent_indices = {}
        self.box_range = {
        'min': [float('inf'), float('inf'), float('inf')],
        'max': [-float('inf'), -float('inf'), -float('inf')]
    }

    def _parse_hierarchy(self, text):
        lines = re.split('\\s*\\n+\\s*', text)

        joint_stack = []

        joint_index = int(0)
        for line in lines:
            words = re.split('\\s+', line)
            instruction = words[0]

            if instruction == "JOINT" or instruction == "ROOT":
                parent = joint_stack[-1] if instruction == "JOINT" else None
                joint = BvhJoint(words[1], parent)
                #
                joint.index = joint_index
                joint_index = joint_index + 1
                #print(f"Joint :{joint.name}, {joint.index}")
                self.joints[joint.name] = joint
                if parent:
                    parent.add_child(joint)
                    #print(f"- parent: {parent.name},{parent.index}")
                joint_stack.append(joint)
                if instruction == "ROOT":
                    self.root = joint
            elif instruction == "CHANNELS":
                for i in range(2, len(words)):
                    joint_stack[-1].channels.append(words[i])
            elif instruction == "OFFSET":
                for i in range(1, len(words)):
                    joint_stack[-1].offset[i - 1] = float(words[i])
            elif instruction == "End":
                joint = BvhJoint(joint_stack[-1].name + "_end", joint_stack[-1])
                joint_stack[-1].add_child(joint)
                joint_stack.append(joint)
                self.joints[joint.name] = joint

                joint.index = joint_index
                joint_index += 1
                #print(f"End Joint :{joint.name}, {joint.index}")

            elif instruction == '}':
                joint_stack.pop()

    def _add_pose_recursive(self, joint, offset, poses):
        pose = joint.offset + offset
        poses.append(pose)

        for c in joint.children:
            self._add_pose_recursive(c, pose, poses)

    def plot_hierarchy(self):
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import axes3d, Axes3D
        poses = []
        self._add_pose_recursive(self.root, np.zeros(3), poses)
        pos = np.array(poses)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(pos[:, 0], pos[:, 2], pos[:, 1])
        ax.set_xlim(-30, 30)
        ax.set_ylim(-30, 30)
        ax.set_zlim(-30, 30)
        plt.show()

    def parse_motion(self, text):
        lines = re.split('\\s*\\n+\\s*', text)

        frame = 0
        for line in lines:
            if line == '':
                continue
            words = re.split('\\s+', line)

            if line.startswith("Frame Time:"):
                self.fps = round(1 / float(words[2]))
                continue
            if line.startswith("Frames:"):
                self.frames = int(words[1])
                continue

            if self.keyframes is None:
                self.keyframes = np.empty((self.frames, len(words)), dtype=np.float32)

            for angle_index in range(len(words)):
                self.keyframes[frame, angle_index] = float(words[angle_index])

            frame += 1

    def parse_string(self, text):
        hierarchy, motion = text.split("MOTION")
        self._parse_hierarchy(hierarchy)
        self.parse_motion(motion)

    def _extract_rotation(self, frame_pose, index_offset, joint):
        local_rotation = np.zeros(3)
        for channel in joint.channels:
            if channel.endswith("position"):
                continue
            if channel == "Xrotation":
                local_rotation[0] = frame_pose[index_offset]
            elif channel == "Yrotation":
                local_rotation[1] = frame_pose[index_offset]
            elif channel == "Zrotation":
                local_rotation[2] = frame_pose[index_offset]
            else:
                raise Exception(f"Unknown channel {channel}")
            index_offset += 1

        local_rotation = np.deg2rad(local_rotation)
        M_rotation = np.eye(3)
        for channel in joint.channels:
            if channel.endswith("position"):
                continue

            if channel == "Xrotation":
                euler_rot = np.array([local_rotation[0], 0., 0.])
            elif channel == "Yrotation":
                euler_rot = np.array([0., local_rotation[1], 0.])
            elif channel == "Zrotation":
                euler_rot = np.array([0., 0., local_rotation[2]])
            else:
                raise Exception(f"Unknown channel {channel}")

            M_channel = euler2mat(*euler_rot)
            M_rotation = M_rotation.dot(M_channel)

        return M_rotation, index_offset

    def _extract_position(self, joint, frame_pose, index_offset):
        offset_position = np.zeros(3)
        for channel in joint.channels:
            if channel.endswith("rotation"):
                continue
            if channel == "Xposition":
                offset_position[0] = frame_pose[index_offset]
            elif channel == "Yposition":
                offset_position[1] = frame_pose[index_offset]
            elif channel == "Zposition":
                offset_position[2] = frame_pose[index_offset]
            else:
                raise Exception(f"Unknown channel {channel}")
            index_offset += 1

        return offset_position, index_offset

    def _recursive_apply_frame(self, joint, frame_pose, index_offset, p, r, M_parent, p_parent, currentFrame):
        if joint.position_animated():
            offset_position, index_offset = self._extract_position(joint, frame_pose, index_offset)
        else:
            offset_position = np.zeros(3)

        joint_index = list(self.joints.values()).index(joint)

        if currentFrame == 0:
            if joint.parent:
                self.node_and_parent_indices[joint_index] = ([joint.index, joint.parent.index])
            else:
                self.node_and_parent_indices[joint_index] = ([joint.index, -1])

        if len(joint.channels) == 0:
            #joint_index = list(self.joints.values()).index(joint)
            p[joint_index] = p_parent + M_parent.dot(joint.offset)
            r[joint_index] = mat2euler(M_parent)
            #print(f"{currentFrame}: r[{joint_index}]: {r[joint_index]}, M_parent: {M_parent}")
            #print(f"{currentFrame}: p[{joint_index}]: {p[joint_index]}")
            return index_offset

        if joint.rotation_animated():
            M_rotation, index_offset = self._extract_rotation(frame_pose, index_offset, joint)
        else:
            M_rotation = np.eye(3)

        M = M_parent.dot(M_rotation)
        position = p_parent + M_parent.dot(joint.offset) + offset_position
        #print(f"{currentFrame}: M_{joint_index}: {M}")
        #print(f": M_mat2euler: {mat2euler(M)}")
        rotation = np.rad2deg(mat2euler(M))

        #joint_index = list(self.joints.values()).index(joint)
        p[joint_index] = position
        r[joint_index] = rotation
        #print(f"{currentFrame}: r[{joint_index}]: {rotation}, M_parent: {M_parent}, M_rotation: {M_rotation}")
        #print(f"{currentFrame}: p[{joint_index}]: {position}")


        for c in joint.children:
            index_offset = self._recursive_apply_frame(c, frame_pose, index_offset, p, r, M, position, currentFrame)

        return index_offset

    def _recursive_apply_frame_local(self, joint, frame_pose, index_offset, p_local, r_local, M_parent, p_parent, currentFrame):
        if joint.position_animated():
            offset_position, index_offset = self._extract_position(joint, frame_pose, index_offset)
        else:
            offset_position = np.zeros(3)

        joint_index = list(self.joints.values()).index(joint)

        if currentFrame == 0:
            if joint.parent:
                self.node_and_parent_indices[joint_index] = ([joint.index, joint.parent.index])
            else:
                self.node_and_parent_indices[joint_index] = ([joint.index, -1])

        if len(joint.channels) == 0:
            #joint_index = list(self.joints.values()).index(joint)
            p_local[joint_index] = joint.offset       #p[joint_index] = p_parent + M_parent.dot(joint.offset)
            r_local[joint_index] = np.zeros(3)                     #r[joint_index] = mat2euler(M_parent)
            #print(f"Joint Channels Empty!! Joint: {joint}")
            return index_offset

        if joint.rotation_animated():
            M_rotation, index_offset = self._extract_rotation(frame_pose, index_offset, joint)
        else:
            M_rotation = np.eye(3)

        M = M_rotation                                             #M = M_parent.dot(M_rotation)
        position = offset_position + joint.offset;                 #position = p_parent + M_parent.dot(joint.offset) + offset_position

        if np.count_nonzero(offset_position) == 3 and np.count_nonzero(joint.offset)==3: #####
            print(f"WARNING!! Joint have position offset at {joint} ({offset_position},{joint.offset}), file name: {self.filename}") #####
        rotation = np.rad2deg(mat2euler(M))
        #joint_index = list(self.joints.values()).index(joint)
        p_local[joint_index] = position
        r_local[joint_index] = rotation
        #print(f"{currentFrame}: r_local[{joint_index}]:  {r_local[joint_index]}")
        #print(f"{currentFrame}: p_local[{joint_index}]:  {p_local[joint_index]}")
        for c in joint.children:
            index_offset = self._recursive_apply_frame_local(c, frame_pose, index_offset, p_local, r_local, M, position, currentFrame)

        return index_offset


    def frame_pose(self, frame):
        p = np.empty((len(self.joints), 3))
        r = np.empty((len(self.joints), 3))
        frame_pose = self.keyframes[frame]
        M_parent = np.zeros((3, 3))
        M_parent[0, 0] = 1
        M_parent[1, 1] = 1
        M_parent[2, 2] = 1
        if frame == 0:
            self.node_and_parent_indices = np.empty((len(self.joints), 2))
        self._recursive_apply_frame(self.root, frame_pose, 0, p, r, M_parent, np.zeros(3), frame)

        return p, r

    def frame_pose_local(self, frame):
        p = np.empty((len(self.joints), 3))
        r = np.empty((len(self.joints), 3))
        frame_pose = self.keyframes[frame]
        #print(f"frame_pose: {frame_pose}")
        M_parent = np.zeros((3, 3))
        M_parent[0, 0] = 1
        M_parent[1, 1] = 1
        M_parent[2, 2] = 1
        if frame == 0:
            self.node_and_parent_indices = np.empty((len(self.joints), 2))
        self._recursive_apply_frame_local(self.root, frame_pose, 0, p, r, M_parent, np.zeros(3), frame)

        return p, r

    def all_frame_poses(self):
        p = np.empty((self.frames, len(self.joints), 3))
        r = np.empty((self.frames, len(self.joints), 3))

        for frame in range(len(self.keyframes)):
            p[frame], r[frame] = self.frame_pose(frame)

        return p, r

    def _plot_pose(self, p, r, fig=None, ax=None):
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import axes3d, Axes3D
        if fig is None:
            fig = plt.figure()
        if ax is None:
            ax = fig.add_subplot(111, projection='3d')

        ax.cla()
        ax.scatter(p[:, 0], p[:, 2], p[:, 1])
        ax.set_xlim(-30, 30)
        ax.set_ylim(-30, 30)
        ax.set_zlim(-1, 59)

        plt.draw()
        plt.pause(0.001)

    def plot_frame(self, frame, fig=None, ax=None):
        p, r = self.frame_pose(frame)
        self._plot_pose(p, r, fig, ax)

    def joint_names(self):
        return self.joints.keys()

    def parse_file(self, path):
        with open(path, 'r') as f:
            self.parse_string(f.read())

    def plot_all_frames(self):
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import axes3d, Axes3D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for i in range(self.frames):
            self.plot_frame(i, fig, ax)

    def __repr__(self):
        return f"BVH {len(self.joints.keys())} joints, {self.frames} frames"

def get_bvh(path):
    anim = Bvh()
    anim.filename = path.split('/')[-1]
    # parser file
    anim.parse_file(path)
    return anim

def get_position_and_rotation(self):
    #print(f"file name: {self.filename}, frames: {self.frames},  fps: {self.fps}")
    self.positions = []
    self.rotations = []
    for i in range(self.frames):
        positions, rotations = self.frame_pose(i)
        self.positions.append(positions)
        self.rotations.append(rotations)
        for p in positions:
            self.box_range['min'][0] = min(self.box_range['min'][0], p[0])
            self.box_range['min'][1] = min(self.box_range['min'][1], p[1])
            self.box_range['min'][2] = min(self.box_range['min'][2], p[2])

            self.box_range['max'][0] = max(self.box_range['max'][0], p[0])
            self.box_range['max'][1] = max(self.box_range['max'][1], p[1])
            self.box_range['max'][2] = max(self.box_range['max'][2], p[2])

    #print(f"i: {i}, box range: {self.box_range} \n p: {self.positions}, \n r: {self.rotations}")
    return self.positions, self.rotations

def get_local_position_and_rotation(self):
    #print(f"file name: {self.filename}, frames: {self.frames},  fps: {self.fps}")
    self.positions = []
    self.rotations = []
    for i in range(self.frames):
        positions, rotations = self.frame_pose_local(i)
        self.positions.append(positions)
        self.rotations.append(rotations)
        for p in positions:
            self.box_range['min'][0] = min(self.box_range['min'][0], p[0])
            self.box_range['min'][1] = min(self.box_range['min'][1], p[1])
            self.box_range['min'][2] = min(self.box_range['min'][2], p[2])

            self.box_range['max'][0] = max(self.box_range['max'][0], p[0])
            self.box_range['max'][1] = max(self.box_range['max'][1], p[1])
            self.box_range['max'][2] = max(self.box_range['max'][2], p[2])

    #print(f"i: {i}, box range: {self.box_range} \n p: {self.positions}")
    #print(f"i: {i}, box range: {self.box_range} \n p: {self.positions}, \n r: {self.rotations}")
    return self.positions, self.rotations


if __name__ == '__main__':
    anim = get_bvh("bvhData/example.bvh")
    get_position_and_rotation(anim)
    get_local_position_and_rotation(anim)
    #print(f"parent indices: {anim.node_and_parent_indices}")

    # # create Bvh parser
    # anim = Bvh()
    # # parser file
    # anim.parse_file("bvhData/example.bvh")
    #
    # # draw the skeleton in T-pose
    # anim.plot_hierarchy()
    #
    # # extract single frame pose: axis0=joint, axis1=positionXYZ/rotationXYZ
    # p, r = anim.frame_pose(0)
    #
    # # extract all poses: axis0=frame, axis1=joint, axis2=positionXYZ/rotationXYZ
    # all_p, all_r = anim.all_frame_poses()
    #
    # # print all joints, their positions and orientations
    # for _p, _r, _j in zip(p, r, anim.joint_names()):
    #     print(f"{_j}: p={_p}, r={_r}")
    #
    # # draw the skeleton for the given frame
    # anim.plot_frame(22)
    #
    # # show full animation
    # anim.plot_all_frames()
