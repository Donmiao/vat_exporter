Shader "Custom/DrawSkeleton"
{
	Properties
	{
		_VertexTex ("VertexTex", 2D) = "white" {}
		_TimeScale ("TimeScale", Float) = 1
        _Scale ("BoundingBoxScale", Vector) = (1, 1, 1)
        _Offset ("BoundingBoxOffset", Vector) = (-0.5, -0.5, -0.5)

		_Point1("Point1",vector) = (100,100,0,0)
		_Point2("Point2",vector) = (200,200,0,0)
		_LP1("linePoint1",vector) = (300,100,0,0)
		_LP2("linePoint2",vector) = (600,400,0,0)
		_LineWidth("LineWidth",range(1,20)) = 2.0
	
	}
	SubShader
	{
		Pass
		{
			CGPROGRAM
			#pragma vertex vert
			#pragma fragment frag
			
			#include "UnityCG.cginc"			
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

			struct appdata
			{
				float4 vertex : POSITION;
                float2 uv : TEXCOORD0;

			};
 
			struct v2f
			{
				float2 uv : TEXCOORD0;
                //float3 normal: NORMAL0;
                float4 vertex : SV_POSITION;
                float3 worldPos: TEXCOORD1;
			};
			float4 _LP1;
			float4 _LP2;
			float _LineWidth;

			sampler2D _MainTex;
            TEXTURE2D(_VertexTex);
            //TEXTURE2D(_NormalTex);
            float4 _BaseColor;
            float4 _MainTex_ST;
            float _TimeScale;
            float3 _Scale;
            float3 _Offset;
            //float _Shininess;

			int3 VAT_SamplePoint(Texture2D map, int i, float t)
            {
                int w, h;
                map.GetDimensions(w, h);
                int frame = t * (h - 1);
                return int3(i, frame, 0);
            }

			void FluidVAT_half(
                Texture2D vertexMap,
                //Texture2D normalMap,
                float3 scale,
                float3 offset,
                int i,
                float t,
                out float3 outPosition,
                //out float3 outNormal
            )
            {
                int3 sp = VAT_SamplePoint(vertexMap, i, t);
                float4 p = vertexMap.Load(sp);
                
                outPosition = p.xyz * scale + offset;
                //outNormal = normalMap.Load(sp);
            }



			v2f vert (appdata v)
			{
				v2f o;
				int i = (int)vid;
                float t = 1.0 - frac(_Time.x * _TimeScale);
                
                float3 worldPosition;
                FluidVAT_half(_VertexTex, _NormalTex, _Scale, _Offset, i, t, worldPosition);
                v.vertex.xyz = worldPosition;
                v.vertex.w = 1.0;
                
                o.vertex = TransformObjectToHClip(v.vertex);
                o.worldPos = TransformObjectToWorld(v.vertex).xyz;
                //o.normal = worldNormal;
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                return o;
			}
			
			fixed4 frag (v2f i) : SV_Target
			{
 
				//绘制直线上两点
				if( pow((i.vertex.x- _LP1.x ),2) + pow((i.vertex.y- _LP1.y ),2) <100   )
				{
					//return fixed4(0,0,1,1);
				}
				if( pow((i.vertex.x- _LP2.x ),2) + pow((i.vertex.y- _LP2.y ),2) <100   )
				{
					//return fixed4(0,0,1,1);
				}
				
				float d = abs((_LP2.y-_LP1.y)*i.vertex.x + (_LP1.x - _LP2.x)*i.vertex.y +_LP2.x*_LP1.y -_LP2.y*_LP1.x )/sqrt(pow(_LP2.y-_LP1.y,2) + pow(_LP1.x-_LP2.x,2));
				
				if(d<=_LineWidth/2)
				{
					//return fixed4(0.8,0.2,0.5,1);
				}

				//////
				// sample the texture
                half4 col = _BaseColor;

                float3 view = normalize(_WorldSpaceCameraPos - i.worldPos);
                //float3 light = normalize(_MainLightPosition - i.worldPos);

                //float intensity = saturate(dot(i.normal, light));
                //float3 h = normalize(view + light);
                //float specAngle = saturate(dot(h, i.normal));
                
                //float3 mainLight = _MainLightColor.xyz;
                float3 diffuse = col.xyz * intensity * mainLight;
                float3 specular = pow(specAngle, _Shininess) * mainLight;

                //return col；
 
				//默认返回白色
				return fixed4(1,1,1,1);
 
			}
			ENDCG
		}
	}
}
