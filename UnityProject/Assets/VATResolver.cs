using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
//using System.Drawing;


public class VATResolver : MonoBehaviour
{

    public Texture2D vertex_texture;
    Color[] rawPixelData;
    int height;
    int width;
    float t = 0;
    public float updateInterval = 0.2f;
    float j = 0;
    // Start is called before the first frame update
    void Start()
    {

        height = vertex_texture.height-1; //For the extra line stores the node_parent_indices info.
        width = vertex_texture.width;
        
            //UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32_SFloat;

        rawPixelData = vertex_texture.GetPixels();
        foreach (var pix in rawPixelData)
        {
            Debug.Log("pix: " + pix.r);
        }
        
        for (int i = 0; i < vertex_texture.width; i++)
        {
            int index_node = (int)Mathf.Round((rawPixelData[i][0]*1000.0f) - 1.0f);
            int index_parent = (int)Mathf.Round((rawPixelData[i][1]*1000.0f) - 1.0f);

            Debug.Log("index node and parent:" + rawPixelData[i] +",    "+ index_node + "," + index_parent);
            
            Debug.DrawLine(Camera.main.transform.position, Vector3.one*100,Color.red);
            if (index_parent > -1)
                Debug.DrawLine(
                    new Vector3(rawPixelData[1 * height + index_node].r, rawPixelData[1 * height + index_node].g, rawPixelData[1 * height + index_node].b)*100,
                    new Vector3(rawPixelData[1 * height + index_parent].r, rawPixelData[1 * height + index_parent].g, rawPixelData[1 * height + index_parent].b)*100);
                    
        }
        //Debug.Log(rawPixelData + "\n " + rawPixelData[0]*100.0f+"," + rawPixelData[1]);
        Debug.Log( vertex_texture.name + ": W /H = " + vertex_texture.width + "/ " + vertex_texture.height);



    }

    // Update is called once per frame
    void OnDrawGizmos()
    {

        t %= (height - 1);

        for (int i = 0; i < vertex_texture.width; i++)
        {
            if (rawPixelData == null || rawPixelData.Length <= i)
                return;
           
            int index_node = (int)(Mathf.Round(rawPixelData[i].r * 1000.0f) - 1);
            int index_parent = (int)(Mathf.Round(rawPixelData[i].g * 1000.0f) - 1);

            //Debug.Log("i: " + i + ", node / parent:" + rawPixelData[i].r + ",    " + index_node + "/" + index_parent);
            if (index_parent > -1)
            {
                Gizmos.DrawSphere(
                new Vector3(rawPixelData[(height - (int)t) * width + index_node].r, rawPixelData[(height - (int)t) * width + index_node].g, rawPixelData[(height - (int)t) * width + index_node].b) * 10,
                0.04f);

                Debug.DrawLine(
                new Vector3(rawPixelData[(height - (int)t) * width + index_node].r, rawPixelData[(height - (int)t) * width + index_node].g, rawPixelData[(height - (int)t) * width + index_node].b) * 10,
                new Vector3(rawPixelData[(height - (int)t) * width + index_parent].r, rawPixelData[(height - (int)t) * width + index_parent].g, rawPixelData[(height - (int)t) * width + index_parent].b) * 10,
                Color.blue);
            }


        }
        t+= Mathf.Clamp(updateInterval, 0, 1); ;

    }

    //void OnDrawGizmos()
    //{

    //    t %= (height - 1);

    //    j %= vertex_texture.width;
    //    for (int i = 0; i < j; i++)
    //    {
    //        if (rawPixelData == null || rawPixelData.Length<=i)
    //            return;
    //        Debug.Log("i: " + i + ", raw data:" + rawPixelData[i]);

    //       int index_node = (int)(Mathf.Round(rawPixelData[i].r * 1000.0f) - 1);
    //       int index_parent = (int)(Mathf.Round(rawPixelData[i].g * 1000.0f) - 1);

    //        Debug.Log("i: " + i + ", node / parent:" + rawPixelData[i].r + ",    " + index_node + "/" + index_parent);
    //               if (index_parent > -1)
    //        {
    //            Gizmos.DrawSphere(
    //            new Vector3(rawPixelData[(height - (int)t) * width + index_node].r, rawPixelData[(height - (int)t) * width + index_node].g, rawPixelData[(height - (int)t) * width + index_node].b) * 10,
    //            0.03f);
    //            Debug.DrawLine(
    //            new Vector3(rawPixelData[(height - (int)t) * width + index_node].r, rawPixelData[(height - (int)t) * width + index_node].g, rawPixelData[(height - (int)t) * width + index_node].b) * 10,
    //            new Vector3(rawPixelData[(height - (int)t) * width + index_parent].r, rawPixelData[(height - (int)t) * width + index_parent].g, rawPixelData[(height - (int)t) * width + index_parent].b) * 10,
    //            Color.blue);
    //        }


    //    }
    //    //j++;
    //    j+= Mathf.Clamp(updateInterval, 0, 1);
    //    // t+= Mathf.Clamp(updateInterval, 0, 1); ;

    //}
}


//using System.Collections;
//using System.Collections.Generic;
//using UnityEngine;
//using UnityEngine.UI;
////using System.Drawing;


//public class VATResolver : MonoBehaviour
//{

//    public Texture2D vertex_texture;
//    Color[] rawPixelData;
//    int height;
//    int width;
//    float t = 0;
//    public float updateInterval = 0.2f;

//    // Start is called before the first frame update
//    void Start()
//    {

//        height = vertex_texture.height - 1; //For the extra line stores the node_parent_indices info.
//        width = vertex_texture.width;

//        rawPixelData = vertex_texture.GetPixels();
//        for (int i = 0; i < vertex_texture.width; i++)
//        {
//            int index_node = (int)(rawPixelData[i][0] * 1000) - 1;
//            int index_parent = (int)(rawPixelData[i][1] * 1000) - 1;

//            //            Debug.Log("index node and parent:" + rawPixelData[i] +",    "+ index_node + "," + index_parent);

//            Debug.DrawLine(Camera.main.transform.position, Vector3.one * 100, Color.red);
//            if (index_parent > -1)
//                Debug.DrawLine(
//                    new Vector3(rawPixelData[1 * height + index_node].r, rawPixelData[1 * height + index_node].g, rawPixelData[1 * height + index_node].b) * 100,
//                    new Vector3(rawPixelData[1 * height + index_parent].r, rawPixelData[1 * height + index_parent].g, rawPixelData[1 * height + index_parent].b) * 100);

//        }
//        //Debug.Log(rawPixelData + "\n " + rawPixelData[0]*100.0f+"," + rawPixelData[1]);
//        Debug.Log(vertex_texture.name + ": W /H = " + vertex_texture.width + "/ " + vertex_texture.height);



//    }

//    // Update is called once per frame
//    void Update()
//    {

//        t %= (height - 1);

//        for (int i = 0; i < vertex_texture.width; i++)
//        {
//            int index_node = (int)(rawPixelData[i][0] * 1000) - 1;
//            int index_parent = (int)(rawPixelData[i][1] * 1000) - 1;

//            //Debug.Log("index node and parent:" + rawPixelData[i] + ",    " + index_node + "," + index_parent);

//            // Debug.DrawLine(Camera.main.transform.position, Vector3.one * 100, Color.red);
//            if (index_parent > -1)
//                Debug.DrawLine(
//                    new Vector3(rawPixelData[(height - (int)t) * width + index_node].r, rawPixelData[(height - (int)t) * width + index_node].g, rawPixelData[(height - (int)t) * width + index_node].b) * 10,
//                    new Vector3(rawPixelData[(height - (int)t) * width + index_parent].r, rawPixelData[(height - (int)t) * width + index_parent].g, rawPixelData[(height - (int)t) * width + index_parent].b) * 10,
//                    Color.blue);

//        }

//        t += Mathf.Clamp(updateInterval, 0, 1); ;

//    }
//}
