"use client";

import { useTranslations } from "next-intl";

type Props = {
  channel: string;
};

function channelClass(channel: string): string {
  if (channel.includes("NAFED") || channel.includes("FCI")) return "channel-govt";
  if (channel.includes("APMC")) return "channel-market";
  return "channel-neutral";
}

export function ChannelBadge({ channel }: Props) {
  const t = useTranslations("rec");
  return (
    <div className="channel-badge-wrap">
      <span className="channel-label">{t("channel")}</span>
      <span className={`channel-badge ${channelClass(channel)}`}>{channel}</span>
    </div>
  );
}
