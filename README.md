# Bvh Texture Generator
 


# Features
- Extract skeleton information and calculate the full pose of each keyframe
- Generate local and world space animation textures where the y-axis represents temporal info and the x-axis represents the position (or rotation) of each node. 
(Four textures could be generated from each bvh file: local /world rotation texture, and local/ world position texture.)
- Verifying the generated textures by converting animation textures back to animations and display in a Unity project.


# How to use 

## Generate local and world animation textures

1. Import python packages according to “/requirements.txt”.
2. Place bvh source files to “/bvhData”.
3. Run the python script “build_vat.py”, and the output files will be saved to “/UnityProject/Assets/bvh/local” or  “/UnityProject/Assets/bvh/world”


## Verify animation texture in Unity

1. Import and open /UnityProject
2. Open Assets/Scenes/SampleScene and run to display the verification demo; or create an empty gameObject and add script “VAT Resolver ” as a new component. Modify the value of vertex_texture and Rotation_texture.
<img width="308" alt="Screenshot 2023-03-08 at 03 54 17" src="https://user-images.githubusercontent.com/29623574/223616093-081a8431-b155-46b9-9513-3fd8d37eaf24.png">
3. Make sure the verified textures are configured as the example:
<img width="301" alt="Screenshot 2023-03-08 at 03 54 36" src="https://user-images.githubusercontent.com/29623574/223616104-b2e70966-f7e1-4a50-9cda-19e9c4f68e29.png">

