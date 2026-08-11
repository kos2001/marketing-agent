import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "center",
          gap: 18,
          paddingBottom: 30,
          background: "#09090b",
        }}
      >
        <div style={{ width: 28, height: 66, background: "#38bdf8", borderRadius: 6 }} />
        <div style={{ width: 28, height: 106, background: "#38bdf8", borderRadius: 6 }} />
        <div style={{ width: 28, height: 146, background: "#38bdf8", borderRadius: 6 }} />
      </div>
    ),
    { ...size },
  );
}
