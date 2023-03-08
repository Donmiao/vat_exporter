# Bvh Texture Generator
 


# Features
- Extract skeleton information and calculate the full pose of each keyframe
- Generate local and world space animation textures where the y-axis represents temporal info and the x-axis represents the position (or rotation) of each node. 
(Four textures could be generated from each bvh file: local /world rotation texture, and local/ world position texture.)
- Verify the generated textures by converting them back to animations, and display the animations in a Unity project.


# How to use 

## Generate local and world animation textures

1. Import python packages according to “/requirements.txt”.
2. Place bvh source files to “/bvhData”.
3. Run the python script “build_vat.py”, and the output files will be saved to “/UnityProject/Assets/bvh/local” or “/UnityProject/Assets/bvh/world”.


## Verify animation texture in Unity

1. Import and open /UnityProject
2. Open Assets/Scenes/SampleScene and run to display the verification demo; or create an empty gameObject and add script “VAT Resolver ” as a new component. Modify the value of vertex_texture and Rotation_texture.
<img width="301" alt="Screenshot 2023-03-08 at 03 59 35" src="https://user-images.githubusercontent.com/29623574/223616400-e06422fe-70a8-405b-b2f5-cdb41614bee9.png">
3. Make sure the verified textures are configured as the example:
<img width="294" alt="Screenshot 2023-03-08 at 04 00 09" src="https://user-images.githubusercontent.com/29623574/223616408-560510a2-0201-45b8-aae0-303695faa1fe.png">


