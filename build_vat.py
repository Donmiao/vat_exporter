#!/usr/local/bin/python3

import json
from math import ceil, log2
from os import listdir
from os.path import getmtime, isfile, join

import imageio
import numpy as np
from lmath import (box_compute_size, box_create, box_expand_box, vector_add,
                   vector_cross, vector_normalize)
from bvh import (get_bvh, get_position_and_rotation, get_local_position_and_rotation)


def calculate_normal(model):
    vertices = model['vertices']
    normals = []

    for _ in vertices:
        n = (0.0, 0.0, 0.0)
        normals.append(n)

    for f in model['faces']:
        i0 = f[0]
        i1 = f[1]
        i2 = f[2]

        v0 = vertices[i0]
        v1 = vertices[i1]
        v2 = vertices[i2]

        n = triangle_cross_vector(v0, v1, v2)
        normals[i0] = vector_add(normals[i0], n)
        normals[i1] = vector_add(normals[i1], n)
        normals[i2] = vector_add(normals[i2], n)

    for i, n in enumerate(normals):
        normals[i] = vector_normalize(n)

    model['normals'] = normals


def triangle_cross_vector(v0, v1, v2):
    ax = v1[0] - v0[0]
    ay = v1[1] - v0[1]
    az = v1[2] - v0[2]

    bx = v2[0] - v0[0]
    by = v2[1] - v0[1]
    bz = v2[2] - v0[2]

    return vector_cross((ax, ay, az), (bx, by, bz))


def save_exr(filename, data):
    imageio.imwrite(filename, data.astype(np.float32))


def save_png(filename, data):
    imageio.imwrite(filename, data.astype(np.float32))


def save_vertices_and_rotations_tiff(output_path, name, data_vertices, data_rotations):
    imageio.imwrite(join(output_path, 'vertex_' + name + '.tif'), data_vertices.astype(np.float32))
    imageio.imwrite(join(output_path, 'rotation_' + name + '.tif'), data_rotations.astype(np.float32))


def save_vertices_and_rotations_png(output_path, name, data_vertices, data_rotations):
    imageio.imwrite(join(output_path, name, '_vertex.png'), data_vertices.astype(np.float32))
    imageio.imwrite(join(output_path, name, '_rotation.png'), data_rotations.astype(np.float32))


def save_meta(filename, box, width, height, fps):
    with open(filename, 'w') as f:
        meta = {
            'width': width,
            'height': height,
            'box': box,
            'fps': fps
        }
        json.dump(meta, f)


def produce_bvh_texture(data_path, output_path="./output/", downsample_rate=1, clip_length=-1, overlap=0,
                        skip_small_clips=False):
    files = [join(data_path, f) for f in listdir(data_path) if isfile(join(data_path, f)) and f.endswith('.bvh')]
    # files.sort(key = lambda x: getmtime(x))

    max_vertex_count = 0
    box = box_create()
    for file in files:
        anim = get_bvh(file)
        positions, rotations = get_position_and_rotation(anim)
        box = anim.box_range
        max_vertex_count = len(positions[0])
        # width = 1 << (ceil(log2(max_vertex_count)))
        # height = 1 << (ceil(log2(model_count)))
        width = max_vertex_count
        height = anim.frames
        print(
            f"=====================================\nCreating world space texture of file name: {anim.filename}, frame counts: {anim.frames}")

        if clip_length > 0:
            length = min(clip_length, height)

            vertex_tex = np.zeros((length + 1, width, 3))  # vertex_tex = np.zeros((height+1, width, 3))
            rotation_tex = np.zeros((length, width, 3))
            clip_count = int(height / (length - overlap))

            print(f"{clip_count} clips with overlap of {overlap}.")
            # clipping_offset = height % clipping_step
            for n in range(clip_count):
                for y in range(length):
                    t = (n * (length - overlap) + y) * downsample_rate
                    if t >= anim.frames:
                        break

                    for i, p in enumerate(positions[t]):
                        # print(f"i: {i}, p: {p}, {len(positions[y])}")
                        v0 = p[0]
                        v1 = p[1]
                        v2 = p[2]

                        vertex_tex[y][i][0] = (v0 + 50.0) / 100.0
                        vertex_tex[y][i][1] = (v1 + 50.0) / 100.0
                        vertex_tex[y][i][2] = (v2 + 50.0) / 100.0

                        ########################################
                        # vertex_tex[t][i][0] = (v0 - box_min[0]) * inv_delta_x
                        # vertex_tex[t][i][1] = (v1 - box_min[1]) * inv_delta_y
                        # vertex_tex[t][i][2] = (v2 - box_min[2]) * inv_delta_z
                    # print(f"{i} ,positions count: {len(positions)}, vertex_tex: {vertex_tex[y][i]}, boxRange: {box_size}")

                    for i, r in enumerate(rotations[t]):
                        r0 = r[0]
                        r1 = r[1]
                        r2 = r[2]

                        rotation_tex[y][i][0] = float(float(r0 + 180.0) / 360.0)
                        rotation_tex[y][i][1] = float(float(r1 + 180.0) / 360.0)
                        rotation_tex[y][i][2] = float(float(r2 + 180.0) / 360.0)
                        # print(f"r: {rotation_tex[y][i]}, r0: {r0}")
                #####
                for i, node_pair in enumerate(anim.node_and_parent_indices):
                    vertex_tex[length][i][0] = float(node_pair[0] + 1) / 1000.0
                    vertex_tex[length][i][1] = float(node_pair[1] + 1) / 1000.0
                    # print(f"node pair: {vertex_tex[height][i][0]}")
                name = str(anim.filename).split('.bvh')[0] + f"_clip_{n}"
                save_vertices_and_rotations_tiff(output_path, 'world_' + name, vertex_tex, rotation_tex)
                # save_vertices_and_rotations_png(output_path, name+'_local', vertex_tex, rotation_tex)
                save_meta(join(output_path, name + '_world_meta.json'), box, max_vertex_count, anim.frames,
                          anim.fps / downsample_rate)
                print(f"save output file of clip {n + 1}/{clip_count} as {name} [{width} , {length}].")

        else:
            vertex_tex = np.zeros(
                (height / downsample_rate + 1, width, 3))  # vertex_tex = np.zeros((height+1, width, 3))
            rotation_tex = np.zeros((height / downsample_rate, width, 3))
            box_min = box['min']
            box_size = box_compute_size(box)

            ######
            inv_delta_x = 1.0 / box_size[0]
            inv_delta_y = 1.0 / box_size[1]
            inv_delta_z = 1.0 / box_size[2]
            # print("normalizing animation data")
            for y in range(height):
                y *= downsample_rate
                if y >= anim.frames:
                    break

                for i, p in enumerate(positions[y]):
                    # print(f"i: {i}, p: {p}, {len(positions[y])}")
                    v0 = p[0]
                    v1 = p[1]
                    v2 = p[2]

                    vertex_tex[y][i][0] = (v0 + 50.0) / 100.0  # (v0 - box_min[0]) / 100.0
                    vertex_tex[y][i][1] = (v1 + 50.0) / 100.0  # (v1 - box_min[1]) / 100.0
                    vertex_tex[y][i][2] = (v2 + 50.0) / 100.0  # (v2 - box_min[2]) / 100.0
                    ########################################
                    # vertex_tex[y][i][0] = (v0 - box_min[0]) * inv_delta_x
                    # vertex_tex[y][i][1] = (v1 - box_min[1]) * inv_delta_y
                    # vertex_tex[y][i][2] = (v2 - box_min[2]) * inv_delta_z
                # print(f"{i} ,positions count: {len(positions)}, vertex_tex: {vertex_tex[y][i]}, boxRange: {box_size}")

                # print(f" vertex_tex: {vertex_tex[0][0]}, boxRange: {box_size}")

                for i, r in enumerate(rotations[y]):
                    r0 = r[0]
                    r1 = r[1]
                    r2 = r[2]

                    rotation_tex[y][i][0] = float(float(r0 + 180.0) / 360.0)
                    rotation_tex[y][i][1] = float(float(r1 + 180.0) / 360.0)
                    rotation_tex[y][i][2] = float(float(r2 + 180.0) / 360.0)
                    # print(f"r: {rotation_tex[y][i]}, r0: {r0}")

            for i, node_pair in enumerate(anim.node_and_parent_indices):
                vertex_tex[height][i][0] = (float)(node_pair[0] + 1) / 1000.0
                vertex_tex[height][i][1] = (float)(node_pair[1] + 1) / 1000.0
                # print(f"node pair: {vertex_tex[height][i][0]}")

            name = str(anim.filename).split('.bvh')[0]
            save_vertices_and_rotations_tiff(output_path, 'world_' + name, vertex_tex, rotation_tex)
            # save_vertices_and_rotations_png(output_path, name, vertex_tex, rotation_tex)
            save_meta(join(output_path, name + '_meta.json'), box, max_vertex_count, anim.frames,
                      anim.fps / downsample_rate)
            print(f"save output file as {name}")


def produce_local_bvh_texture(data_path, output_path="./output/", downsample_rate=1, clip_length=-1, overlap=0,
                              skip_small_clips=False):
    total_output_count = 0
    files = [join(data_path, f) for f in listdir(data_path) if isfile(join(data_path, f)) and f.endswith('.bvh')]
    # files.sort(key = lambda x: getmtime(x))

    max_vertex_count = 0
    box = box_create()
    for file in files:
        anim = get_bvh(file)
        positions_local, rotations_local = get_local_position_and_rotation(anim)
        positions_world, rotations_world = get_position_and_rotation(anim)
        box = anim.box_range
        max_vertex_count = len(positions_local[0])
        # width = 1 << (ceil(log2(max_vertex_count)))
        # height = 1 << (ceil(log2(model_count)))
        width = max_vertex_count
        height = anim.frames
        if (skip_small_clips and clip_length > height):
            continue
        print(f"=====================================\nCreating local texture of {anim.filename} [{width}, {height}]")

        box_min = box['min']
        box_size = box_compute_size(box)
        inv_delta_x = 1.0 / box_size[0]
        inv_delta_y = 1.0 / box_size[1]
        inv_delta_z = 1.0 / box_size[2]

        clipping_times = 0
        clipping_offset = 0
        if clip_length > 0:
            length = min(clip_length, height)

            vertex_tex = np.zeros((length + 1, width, 3))  # vertex_tex = np.zeros((height+1, width, 3))
            rotation_tex = np.zeros((length, width, 3))
            clip_count = int(height / (length - overlap))

            print(
                f"height: {height}, clip_length: {length}, overlap:{overlap}, clip_count:{clip_count}, downsample_rate:{downsample_rate}")
            print(f"{clip_count} clips with overlap of {overlap}.")
            # clipping_offset = height % clipping_step
            for n in range(clip_count):
                for y in range(length):
                    t = (n * (length - overlap) + y) * downsample_rate + (n % downsample_rate)

                    if t >= anim.frames:
                        break

                    if y > 0:
                        position_enumerate = enumerate(positions_local[t])
                    else:
                        position_enumerate = enumerate(positions_world[t])

                    for i, p in position_enumerate:
                        # print(f"i: {i}, p: {p}, {len(positions[y])}")
                        v0 = p[0]
                        v1 = p[1]
                        v2 = p[2]

                        vertex_tex[y][i][0] = (v0 + 50.0) / 100.0
                        vertex_tex[y][i][1] = (v1 + 50.0) / 100.0
                        vertex_tex[y][i][2] = (v2 + 50.0) / 100.0

                        ########################################
                        # vertex_tex[t][i][0] = (v0 - box_min[0]) * inv_delta_x
                        # vertex_tex[t][i][1] = (v1 - box_min[1]) * inv_delta_y
                        # vertex_tex[t][i][2] = (v2 - box_min[2]) * inv_delta_z
                    # print(f"{i} ,positions count: {len(positions)}, vertex_tex: {vertex_tex[y][i]}, boxRange: {box_size}")

                    # print(f" vertex_tex: {vertex_tex[0][0]}, boxRange: {box_size}")

                    for i, r in enumerate(rotations_local[t]):
                        r0 = r[0]
                        r1 = r[1]
                        r2 = r[2]

                        rotation_tex[y][i][0] = float(float(r0 + 180.0) / 360.0)
                        rotation_tex[y][i][1] = float(float(r1 + 180.0) / 360.0)
                        rotation_tex[y][i][2] = float(float(r2 + 180.0) / 360.0)
                        # print(f"r: {rotation_tex[y][i]}, r0: {r0}")
                #####
                for i, node_pair in enumerate(anim.node_and_parent_indices):
                    vertex_tex[length][i][0] = (float)(node_pair[0] + 1) / 1000.0
                    vertex_tex[length][i][1] = (float)(node_pair[1] + 1) / 1000.0
                    # print(f"node pair: {vertex_tex[height][i][0]}")
                name = str(anim.filename).split('.bvh')[0] + f"_clip_{n}"
                save_vertices_and_rotations_tiff(output_path, 'local_' + name, vertex_tex, rotation_tex)
                # save_vertices_and_rotations_png(output_path, name+'_local', vertex_tex, rotation_tex)
                save_meta(join(output_path, name + '_local_meta.json'), box, max_vertex_count, anim.frames,
                          anim.fps / downsample_rate)
                # print(f"save output file of clip {n + 1}/{clip_count} as {name} [{width} , {length}].")
                total_output_count += 1

        else:
            vertex_tex = np.zeros(
                (height / downsample_rate + 1, width, 3))  # vertex_tex = np.zeros((height+1, width, 3))
            rotation_tex = np.zeros((height / downsample_rate, width, 3))
            # print("normalizing animation data")
            for y in range(height):
                y *= downsample_rate
                if y >= anim.frames:
                    break
                for i, p in enumerate(positions_local[y]):
                    # print(f"i: {i}, p: {p}, {len(positions[y])}")
                    v0 = p[0]
                    v1 = p[1]
                    v2 = p[2]

                    vertex_tex[y][i][0] = (v0 + 50.0) / 100.0
                    vertex_tex[y][i][1] = (v1 + 50.0) / 100.0
                    vertex_tex[y][i][2] = (v2 + 50.0) / 100.0

                    ########################################
                    # vertex_tex[y][i][0] = (v0 - box_min[0]) * inv_delta_x
                    # vertex_tex[y][i][1] = (v1 - box_min[1]) * inv_delta_y
                    # vertex_tex[y][i][2] = (v2 - box_min[2]) * inv_delta_z
                # print(f"{i} ,positions count: {len(positions)}, vertex_tex: {vertex_tex[y][i]}, boxRange: {box_size}")

                # print(f" vertex_tex: {vertex_tex[0][0]}, boxRange: {box_size}")

                for i, r in enumerate(rotations_local[y]):
                    r0 = r[0]
                    r1 = r[1]
                    r2 = r[2]

                    rotation_tex[y][i][0] = float(float(r0 + 180.0) / 360.0)
                    rotation_tex[y][i][1] = float(float(r1 + 180.0) / 360.0)
                    rotation_tex[y][i][2] = float(float(r2 + 180.0) / 360.0)
                    # print(f"r: {rotation_tex[y][i]}, r0: {r0}")

            for i, node_pair in enumerate(anim.node_and_parent_indices):
                vertex_tex[height][i][0] = (float)(node_pair[0] + 1) / 1000.0
                vertex_tex[height][i][1] = (float)(node_pair[1] + 1) / 1000.0
                # print(f"node pair: {vertex_tex[height][i][0]}")

            name = str(anim.filename).split('.bvh')[0]
            save_vertices_and_rotations_tiff(output_path, 'local_' + name, vertex_tex, rotation_tex)
            # save_vertices_and_rotations_png(output_path, name+'_local', vertex_tex, rotation_tex)
            save_meta(join(output_path, name + '_local_meta.json'), box, max_vertex_count, anim.frames,
                      anim.fps / downsample_rate)
            total_output_count += 1
            print(f"save output file as {name}")

    return total_output_count


if __name__ == '__main__':
    # produce_bvh_texture('bvhData', './UnityProject/Assets/bvh/world')
    # produce_local_bvh_texture('bvhData/Test', './UnityProject/Assets/bvh/local')
    total_count_dataset1 = produce_local_bvh_texture('bvhData/data_1', './UnityProject/Assets/bvh/local/result_clips_1', 4, 80, 16,True)
    total_count_dataset2 = 0 #produce_local_bvh_texture('bvhData/data_2', './UnityProject/Assets/bvh/local/result_clips_2', 4, 80, 16,True)

    print(f"total output: {total_count_dataset1+total_count_dataset2}({total_count_dataset1} from dataset_1 and {total_count_dataset2} from dataset_2)")
    # produce_bvh_texture('bvhData/Test', './UnityProject/Assets/bvh/world',20,1)
