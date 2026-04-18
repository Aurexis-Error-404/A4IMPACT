import Head from "next/head";
import VoiceButton from "@/components/VoiceButton";

export default function Home() {
  return (
    <>
      <Head>
        <title>KrishiCFO</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&family=Lora:ital,wght@0,400;0,500;1,400&family=Martian+Mono:wght@300;400;500&display=swap"
          rel="stylesheet"
        />
      </Head>
      <main style={styles.main}>
        <h1 style={styles.title}>
          Krishi<em style={styles.em}>CFO</em>
        </h1>
        <p style={styles.sub}>Telugu commodity intelligence · Voice + Dashboard</p>
        <VoiceButton />
      </main>
    </>
  );
}

const styles: Record<string, React.CSSProperties> = {
  main: {
    background: "#0b0e0b",
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 24,
    fontFamily: "'Lora', Georgia, serif",
  },
  title: {
    fontFamily: "'Fraunces', serif",
    fontSize: 48,
    fontWeight: 600,
    color: "#f0ece2",
    margin: 0,
  },
  em: {
    fontStyle: "italic",
    color: "#ef9f27",
    fontWeight: 300,
  },
  sub: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 11,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: "#9aa293",
    margin: 0,
  },
};
