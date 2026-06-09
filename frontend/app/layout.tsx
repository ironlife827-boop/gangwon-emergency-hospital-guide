import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "강원 응급 병원 안내",
  description:
    "자연어 증상 입력을 기반으로 의심 질환, 응급도, 강원도 추천 병원을 안내하는 웹 서비스입니다.",
  openGraph: {
    title: "강원 응급 병원 안내",
    description:
      "네이버 지식인 증상 사례 기반 모델로 의심 질환과 추천 진료과를 예측하고 가까운 병원을 안내합니다.",
    type: "website",
    locale: "ko_KR",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
