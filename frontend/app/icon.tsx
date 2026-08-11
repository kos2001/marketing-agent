import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

// 오름차순 막대 3개 — "전략의 3축"과 성과 개선(성장) 진단이라는 이 앱의
// 두 축을 하나의 마크로 겹친다. zinc-950/sky-400은 대시보드 배색 그대로.
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "center",
          gap: 3,
          paddingBottom: 5,
          background: "#09090b",
          borderRadius: 7,
        }}
      >
        <div style={{ width: 5, height: 12, background: "#38bdf8", borderRadius: 1 }} />
        <div style={{ width: 5, height: 19, background: "#38bdf8", borderRadius: 1 }} />
        <div style={{ width: 5, height: 26, background: "#38bdf8", borderRadius: 1 }} />
      </div>
    ),
    { ...size },
  );
}
