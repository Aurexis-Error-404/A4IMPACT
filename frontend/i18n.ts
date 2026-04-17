import { getRequestConfig } from 'next-intl/server';
import { locales, defaultLocale } from './i18n-config';
import { cookies } from 'next/headers';

export default getRequestConfig(async () => {
  const cookieStore = cookies();
  const rawLocale = cookieStore.get("locale")?.value ?? defaultLocale;
  const locale = locales.includes(rawLocale as any) ? rawLocale : defaultLocale;

  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default
  };
});
