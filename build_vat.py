#!/usr/local/bin/python3

import json
from math import ceil, log2
from os import listdir
from os.path import getmtime, isfile, join

import imageio
import numpy as np
from lmath import (box_compute_size, box_create, box_expand_box, vector_add,
                   vector_cross, vector_normalize)
from bvh import (get_bvh, get_position_and_rotation)

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

def save_vertices_and_rotations_tiff(output_path, filename, data_vertices, data_rotations):
    name = str(filename).split('.bvh')[0]
    imageio.imwrite(join(output_path, name+'_vertex.tif'), data_vertices.astype(np.float32))
    imageio.imwrite(join(output_path, name+'_rotation.tif'), data_rotations.astype(np.float32))


def save_vertices_and_rotations_png(output_path, filename, data_vertices, data_rotations):
    name = str(filename).split('.bvh')[0]
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

def main(data_path, output_path="./output/"):
    files = [join(data_path, f) for f in listdir(data_path) if isfile(join(data_path, f)) and f.endswith('.bvh')]
    #files.sort(key = lambda x: getmtime(x))

    max_vertex_count = 0
    box = box_create()
    for file in files:
        anim = get_bvh(file)
        positions, rotations = get_position_and_rotation(anim)
        box = anim.box_range
        #print(f"file name: {anim.filename}, frame counts: {anim.frames}, \nbox:{box}, \n nodes and parent index: {anim.node_and_parent_indices} ")

        max_vertex_count = len(positions[0])
    
    # model_count = len(models)
    # print("max vertex count " + str(max_vertex_count))
    # print("frame count " + str(model_count))

    # width = 1 << (ceil(log2(max_vertex_count)))
    # height = 1 << (ceil(log2(model_count)))
        width = max_vertex_count

        height = anim.frames
        print("create output texture [{}, {}]".format(width, height))

        vertex_tex = np.zeros((height + 1, width, 3)) #vertex_tex = np.zeros((height+1, width, 3))
        rotation_tex = np.zeros((height, width, 3))

        box_min = box['min']
        box_size = box_compute_size(box)

        ######
        # inv_delta_x = 1.0 / box_size[0]
        # inv_delta_y = 1.0 / box_size[1]
        # inv_delta_z = 1.0 / box_size[2]
        inv_delta_x = 1.0 / 100.0
        inv_delta_y = 1.0 / 100.0
        inv_delta_z = 1.0 / 100.0

        #print("normalizing animation data")
        for y in range(height):
            if y >= anim.frames:
                break

            for i, p in enumerate(positions[y]):
                #print(f"i: {i}, p: {p}, {len(positions[y])}")
                v0 = p[0]
                v1 = p[1]
                v2 = p[2]

                vertex_tex[y][i][0] = (v0 - box_min[0]) / 100.0
                vertex_tex[y][i][1] = (v1 - box_min[1]) / 100.0
                vertex_tex[y][i][2] = (v2 - box_min[2]) / 100.0
                ########################################
                # vertex_tex[y][i][0] = (v0 - box_min[0]) * inv_delta_x
                # vertex_tex[y][i][1] = (v1 - box_min[1]) * inv_delta_y
                # vertex_tex[y][i][2] = (v2 - box_min[2]) * inv_delta_z
               # print(f"{i} ,positions count: {len(positions)}, vertex_tex: {vertex_tex[y][i]}, boxRange: {box_size}")

            #print(f" vertex_tex: {vertex_tex[0][0]}, boxRange: {box_size}")


            for i, r in enumerate(rotations[y]):
                r0 = r[0]
                r1 = r[1]
                r2 = r[2]

                rotation_tex[y][i][0] = float(float(r0 + 180.0) / 360.0)
                rotation_tex[y][i][1] = float(float(r1 + 180.0) / 360.0)
                rotation_tex[y][i][2] = float(float(r2 + 180.0) / 360.0)
                #print(f"r: {rotation_tex[y][i]}, r0: {r0}")

        for i, node_pair in enumerate(anim.node_and_parent_indices):
            vertex_tex[height][i][0] = (float)(node_pair[0]+1)/1000.0
            vertex_tex[height][i][1] = (float)(node_pair[1]+1)/1000.0
            print(f"node pair: {vertex_tex[height][i][0]}")

        print("save output file")

        save_vertices_and_rotations_tiff(output_path, anim.filename, vertex_tex, rotation_tex)
        #save_vertices_and_rotations_png(output_path, anim.filename, vertex_tex, rotation_tex)
        #save_meta(join(output_path, 'meta.json'), box, max_vertex_count, anim.frames, anim.fps)

        name = str(anim.filename).split('.bvh')[0]
        save_meta(join(output_path, name + '_meta.json'), box, max_vertex_count, anim.frames, anim.fps)

        # import tifffile as tiff
        # img = tiff.imread('./output/example_vertex.tif')
        # print(img.shape)  # (9, 20)
        # print(type(img))  # <class 'numpy.ndarray'>
        # print(type(img[0][0]))  # <class 'numpy.uint16'>
        # for img_last_line in img[height]:
        #     print(img_last_line)
       # tiff.imsave('./data_create/v.tif', img)


if __name__ == '__main__':
    main('bvhData')