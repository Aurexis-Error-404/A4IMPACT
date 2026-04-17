"use client";

import { useTranslations } from "next-intl";
import { AlertItem } from "../lib/canned-data";

type Props = {
  alerts: AlertItem[];
};

export function AlertSeverityStack({ alerts }: Props) {
  const t = useTranslations("alerts");

  if (alerts.length === 0) {
    return (
      <div className="alert green">
        <div className="headline">{t("noAlerts")}</div>
        <div className="detail">{t("noAlertsDetail")}</div>
      </div>
    );
  }

  return (
    <div className="alert-stack stagger">
      {alerts.map((alert) => (
        <div key={alert.id} className={`alert ${alert.severity}`}>
          <div className="headline">{alert.headline}</div>
          <div className="detail">{alert.detail}</div>
          <div className="meta">
            {alert.group} - {alert.season}
          </div>
        </div>
      ))}
    </div>
  );
}
