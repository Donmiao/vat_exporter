using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEditor.ShaderGraph.Internal;
using UnityEngine;
using UnityEngine.TextCore.Text;
using UnityEngine.UI;
//using System.Drawing;


public struct bvhMeta
{
    public int width;
    public int height;
    public KeyValuePair<string, Vector3> box;
    public int fps;
}
    public class VATResolver : MonoBehaviour
{

    public Texture2D vertex_texture;
    public Texture2D rotation_texture;
    public int currentFrame = 0;
    public Color displayColour = Color.blue;
    Color[] rawPixelData_vertex;
    Color[] rawPixelData_rotation;
    Vector3[] WorldPosition;
    Matrix4x4[] localToWorldRotation_M;
    int height;
    int width;
    float t = 0;
    public float updateInterval = 0.2f;
    public bool isLocalTexture = false;
    float j = 0;
    // Start is called before the first frame update
    void Start()
    {
        //For the extra line stores the node_parent_indices info.
        height = vertex_texture.height-1; 
        width = vertex_texture.width;
        rawPixelData_vertex = vertex_texture.GetPixels();
        WorldPosition = new Vector3[height * width];
        localToWorldRotation_M = new Matrix4x4[height * width];
        Debug.Log(vertex_texture.name + ": W /H = " + vertex_texture.width + "/ " + vertex_texture.height);

        // Compute World position from local offsets of both Rotation texture and Position texture if using local animation textures.
        if (isLocalTexture)
        {
            rawPixelData_rotation = rotation_texture.GetPixels();

            for (int i = 0; i < height-1; i++)
            {
                Matrix4x4 M_parent = new Matrix4x4();

                var isEndSite = true;

                for (int j = 0; j < width; j++)
                {
                    int index_node = (int)Mathf.Round((rawPixelData_vertex[j][0] * 1000.0f) - 1.0f);
                    int index_parent = (int)Mathf.Round((rawPixelData_vertex[j][1] * 1000.0f) - 1.0f);


                    var col_vert = rawPixelData_vertex[(height - 1 - i) * width + index_node];
                    var col_rota = rawPixelData_rotation[(height - 1 - i) * width + index_node];

                    var offset_position = new Vector4(col_vert.r - 0.5f, col_vert.g - 0.5f, col_vert.b - 0.5f, 0.0f) * 100.0f;
                    var offset_rotation_degree = new Vector4(col_rota.r - 0.5f, col_rota.g - 0.5f, col_rota.b - 0.5f, 0.0f) * 360.0f;
                    var offset_rotation = offset_rotation_degree * Mathf.Deg2Rad;

                    var offset_rotation_mat = Matrix4x4.Rotate(Quaternion.Euler(new Vector3(offset_rotation_degree.x, offset_rotation_degree.y, offset_rotation_degree.z)));
                    offset_rotation_mat.m33 = 0.0f;
                    offset_rotation_mat = ExtractMatrixFromEuler_ZYX(offset_rotation_degree);


                    if ((j + 1 < width) && ((int)Mathf.Round((rawPixelData_vertex[j+1][1] * 1000.0f) - 1.0f) == index_node))
                    {
                        isEndSite = false;
                    }                 
                    // Get world positions using rotation matrices and positions of parents.
                    if (index_parent > -1)
                    {
                        
                        M_parent = localToWorldRotation_M[i * width + index_parent];

                        var parent_position = WorldPosition[i * width + index_parent];

                        localToWorldRotation_M[i * width + index_node] = M_parent * offset_rotation_mat;

                        WorldPosition[i * width + index_node] =  parent_position + M_parent.MultiplyVector(offset_position);

                        if (isEndSite)
                        {
                            localToWorldRotation_M[i * width + index_node] = M_parent;
                        }
                        //Debug.Log(i+": localToWorldRotation[" +  index_node + "] : " + localToWorldRotation[i * width + index_node] );

                    }
                    // Root nodes.
                    else
                    {
                        M_parent = new Matrix4x4();
                        M_parent.m00 = 1.0f;
                        M_parent.m11 = 1.0f;
                        M_parent.m22 = 1.0f;
                        M_parent.m33 = 0.0f;

                        WorldPosition[i * width + index_node] = new Vector3(offset_position.x, offset_position.y, offset_position.z); //M_parent.MultiplyVector(offset_position);
                        localToWorldRotation_M[i * width + index_node] = M_parent * offset_rotation_mat;
                        //Debug.Log(i+ ": localToWorldPosition[" + index_node + "] : " + localToWorldPosition[i * width + index_node]);
                        
                    }

                }
            }
        }
        // Otherwise store the worldspace positions directly.
        else
        {
            for (int i = 0; i < height; i++)
            {
                for (int j = 0; j < width; j++)
                {
                    
                    int index_node = (int)Mathf.Round((rawPixelData_vertex[j][0] * 1000.0f) - 1.0f);
                    if ((height - i) * width + index_node >= rawPixelData_vertex.Length)
                        continue;
                    //int index_parent = (int)Mathf.Round((rawPixelData_vertex[j][1] * 1000.0f) - 1.0f);
                    Debug.Log("i: " + i + ", height:" + height + ", rawPixelData_vertex: " + rawPixelData_vertex.Length+", index: "+ ((height - i) * width + index_node).ToString() + "index_node: "+ index_node);
                    var col_vert = rawPixelData_vertex[(height - i) * width + index_node];
                    if(i * width + index_node< WorldPosition.Length)
                    WorldPosition[i * width + index_node] = new Vector3(col_vert.r - 0.5f, col_vert.g - 0.5f, col_vert.b - 0.5f) * 100.0f;

                }
            }

        }

    }

    // Update is called once per frame
    // To display stored skeletal motion clips.
    void OnDrawGizmos()
    {

        t %= (height - 1);
        
        
         for (int i = 0; i < width; i++)
         {
              if (rawPixelData_vertex == null || rawPixelData_vertex.Length <= i || WorldPosition == null)
                  return;

              int index_node = (int)(Mathf.Round(rawPixelData_vertex[i].r * 1000.0f) - 1);
              int index_parent = (int)(Mathf.Round(rawPixelData_vertex[i].g * 1000.0f) - 1);

              // Draw lines between joint nodes and parent joint nodes.
              if (index_parent > -1)
              {
                Gizmos.DrawSphere(
                WorldPosition[(int)t * width + index_node] + transform.position,
                0.4f);

                Debug.DrawLine(
                WorldPosition[(int)t * width + index_node] + transform.position,
                WorldPosition[(int)t * width + index_parent] + transform.position,
                displayColour);

                currentFrame = Math.Clamp(currentFrame, 0, height - 1);
                if (currentFrame > 0)
                    Debug.DrawLine(
                    WorldPosition[(int)currentFrame * width + index_node] + transform.position,
                    WorldPosition[(int)currentFrame * width + index_parent] + transform.position,
                    Color.red);               
              }
         }
        
        t += Mathf.Clamp(updateInterval, 0, 1);

    }

    //Auxiliary functions.
    public static Quaternion QuaternionFromMatrix(Matrix4x4 m)
    {
        Quaternion q = new Quaternion();
        q.w = Mathf.Sqrt(Mathf.Max(0, 1 + m[0, 0] + m[1, 1] + m[2, 2])) / 2;
        q.x = Mathf.Sqrt(Mathf.Max(0, 1 + m[0, 0] - m[1, 1] - m[2, 2])) / 2;
        q.y = Mathf.Sqrt(Mathf.Max(0, 1 - m[0, 0] + m[1, 1] - m[2, 2])) / 2;
        q.z = Mathf.Sqrt(Mathf.Max(0, 1 - m[0, 0] - m[1, 1] + m[2, 2])) / 2;
        q.x *= Mathf.Sign(q.x * (m[2, 1] - m[1, 2]));
        q.y *= Mathf.Sign(q.y * (m[0, 2] - m[2, 0]));
        q.z *= Mathf.Sign(q.z * (m[1, 0] - m[0, 1]));
        return q;
    }
    public static Quaternion QuaternionFromMatrixFast(Matrix4x4 m)
    {
        return Quaternion.LookRotation(m.GetColumn(2), m.GetColumn(1));
    }

    private void ReadJson(string jsonPath)
    {
        if (File.Exists(jsonPath))
        {
            string jsonString = File.ReadAllText(jsonPath);
            bvhMeta meta = JsonUtility.FromJson<bvhMeta>(jsonString);
            Debug.Log("width：" + meta.width);
            //float[] value;
            //meta.box.("min", out value);
            Debug.Log("box：" + meta.box.ToString());
        }
    }


    public static Matrix4x4 Eul2RotMat4x4(double[] eulerAngles, bool isRadiant = false)
    {
        if (eulerAngles.Length != 3)
            throw new ArgumentOutOfRangeException("The vector eulerAngles must have 3 elements (Rx, Ry, Rz).");
        double[] ct = new double[3];
        double[] st = new double[3];
        // calculate sin and cos of euler angles
        for (int i = 0; i < eulerAngles.Length; i++)
        {
            if (!isRadiant)
                eulerAngles[i] *= Math.PI / 180.0f;
            ct[i] = Math.Cos(eulerAngles[i]);
            st[i] = Math.Sin(eulerAngles[i]);
        }
        Matrix4x4 R = new Matrix4x4();

        R.m00 = (float)(ct[1] * ct[2]);
        R.m01 = (float)(-ct[1] * st[2]);
        R.m02 = (float)st[1];
        R.m10 = (float)(ct[0] * st[2] + ct[2] * st[0] * st[1]);
        R.m11 = (float)(ct[0] * ct[2] - st[0] * st[1] * st[2]);
        R.m12 = (float)(-ct[1] * st[0]);
        R.m20 = (float)(st[0] * st[2] - ct[0] * ct[2] * st[1]);
        R.m21 = (float)(ct[2] * st[0] + ct[0] * st[1] * st[2]);
        R.m22 = (float)(ct[0] * ct[1]);

        return R;
    }
    public static Matrix4x4 ExtractMatrixFromEuler_ZYX(Vector3 rotation_degree){
        Matrix4x4 mat = new Matrix4x4();
        var rotation_radians = rotation_degree * Mathf.Deg2Rad;
        var M_rotation = new Matrix4x4();
        M_rotation.m00 = 1.0f;
        M_rotation.m11 = 1.0f;
        M_rotation.m22 = 1.0f;

        var m_channel_z = Eul2RotMat4x4(new double[] { 0, 0, rotation_degree.z });
        M_rotation = M_rotation * m_channel_z;
        var m_channel_y = Eul2RotMat4x4(new double[] { 0, rotation_degree.y, 0 });
        M_rotation = M_rotation * m_channel_y;
        var m_channel_x = Eul2RotMat4x4(new double[] { rotation_degree.x, 0, 0 });
        M_rotation = M_rotation * m_channel_x;

        return M_rotation;
    }
    public static double[,] Eul2RotM(double[] eulerAngles, bool isRadiant = false)
    {
        if (eulerAngles.Length != 3)
            throw new ArgumentOutOfRangeException("The vector eulerAngles must have 3 elements (Rx, Ry, Rz).");
        double[] ct = new double[3];
        double[] st = new double[3];
        // calculate sin and cos of euler angles
        for (int i = 0; i < eulerAngles.Length; i++)
        {
            if (!isRadiant)
                eulerAngles[i] *= Math.PI / 180;
            ct[i] = Math.Cos(eulerAngles[i]);
            st[i] = Math.Sin(eulerAngles[i]);
        }
        double[,] R = new double[3, 3];

                R[0, 0] = ct[1] * ct[2];
                R[0, 1] = -ct[1] * st[2];
                R[0, 2] = st[1];
                R[1, 0] = ct[0] * st[2] + ct[2] * st[0] * st[1];
                R[1, 1] = ct[0] * ct[2] - st[0] * st[1] * st[2];
                R[1, 2] = -ct[1] * st[0];
                R[2, 0] = st[0] * st[2] - ct[0] * ct[2] * st[1];
                R[2, 1] = ct[2] * st[0] + ct[0] * st[1] * st[2];
                R[2, 2] = ct[0] * ct[1];
      
        return R;
    }



    public static Vector3 QuaternionToEuler(Quaternion q1)
    {
        float sqw = q1.w * q1.w;
        float sqx = q1.x * q1.x;
        float sqy = q1.y * q1.y;
        float sqz = q1.z * q1.z;
        float unit = sqx + sqy + sqz + sqw; // if normalised is one, otherwise is correction factor
        float test = q1.x * q1.w - q1.y * q1.z;
        Vector3 v;

        if (test > 0.4995f * unit)
        { // singularity at north pole
            v.y = 2f * Mathf.Atan2(q1.y, q1.x);
            v.x = Mathf.PI / 2;
            v.z = 0;
            return NormalizeAngles(v * Mathf.Rad2Deg);
        }
        if (test < -0.4995f * unit)
        { // singularity at south pole
            v.y = -2f * Mathf.Atan2(q1.y, q1.x);
            v.x = -Mathf.PI / 2;
            v.z = 0;
            return NormalizeAngles(v * Mathf.Rad2Deg);
        }
        Quaternion q = new Quaternion(q1.w, q1.z, q1.x, q1.y);
        v.y = (float)Math.Atan2(2f * q.x * q.w + 2f * q.y * q.z, 1 - 2f * (q.z * q.z + q.w * q.w));     // Yaw
        v.x = (float)Math.Asin(2f * (q.x * q.z - q.w * q.y));                             // Pitch
        v.z = (float)Math.Atan2(2f * q.x * q.y + 2f * q.z * q.w, 1 - 2f * (q.y * q.y + q.z * q.z));      // Roll
        return NormalizeAngles(v * Mathf.Rad2Deg);
    }

    static Vector3 NormalizeAngles(Vector3 angles)
    {
        angles.x = NormalizeAngle(angles.x);
        angles.y = NormalizeAngle(angles.y);
        angles.z = NormalizeAngle(angles.z);      
        return angles;
    }

    static float NormalizeAngle(float angle)
    {
        while (angle > 360)
            angle -= 360;
        while (angle < 0)
            angle += 360;
        return angle;
    }

}

