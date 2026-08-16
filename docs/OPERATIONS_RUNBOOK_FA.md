# راهنمای انتشار و بازگشت Rvion

این راهنما برای انتشارهای معمول Rvion روی production است. هیچ کلید، رمز، دادهٔ مشتری یا backup را در Git، ticket یا پیام عمومی وارد نکنید.

## پیش از انتشار

در ریشهٔ پروژه و با محیط مجازی محلی اجرا کنید:

```bash
./release-check.sh
```

نتیجه باید بدون خطا باشد. این دستور checkهای Django، عدم اختلاف migration، وابستگی‌های Python، تست‌ها، اعتبارسنجی بانک سؤال، static و benchmark کوتاه را بررسی می‌کند.

مواردی که باید به‌صورت دستی و بدون استفاده از دادهٔ واقعی مشتری بررسی شوند:

- صفحهٔ اصلی و مسیرهای `/fa/` و `/en/` در موبایل و دسکتاپ؛
- ثبت‌نام، دریافت و ورود کد OTP با حساب آزمایشی؛
- ثبت فرم نیازسنجی و ایجاد/نمایش قرارداد با نمونهٔ آزمایشی؛
- ثبت رسید پرداخت آزمایشی و نمایش آن در Inbox؛
- پاسخ به یک تیکت آزمایشی و مشاهدهٔ Timeline.

## انتشار استاندارد

کد را ابتدا به `main` push کنید. سپس روی سرور با کاربر SSH مجاز اجرا کنید:

```bash
ssh ubuntu@SERVER_IP
sudo git -c safe.directory=/srv/arvion -C /srv/arvion fetch origin main
sudo git -c safe.directory=/srv/arvion -C /srv/arvion reset --hard origin/main
sudo /srv/arvion/ops/release.sh
curl -fsS https://rvionai.com/health/
```

`release.sh` قبل از هر تغییر یک snapshot فشرده از PostgreSQL می‌سازد، migrationها و static را اجرا می‌کند، timerهای عملیاتی را فعال نگه می‌دارد، سرویس را restart می‌کند و health check داخلی را تا ۱۵ ثانیه بررسی می‌کند. پس از موفقیت، نسخه و مسیر snapshot در فایل محافظت‌شدهٔ زیر ثبت می‌شود:

```text
/srv/arvion/backups/release-history.log
```

## کنترل پس از انتشار

- `/health/` باید HTTP 200 و `{"status":"ok"}` برگرداند.
- `systemctl is-active arvion` باید `active` باشد.
- در مرکز مدیریت، صف «فوری» و Inbox را برای خطای تازه بررسی کنید.
- فرم عمومی، OTP، پرداخت کارت‌به‌کارت، آزمون و لینک قرارداد را با دادهٔ آزمایشی مرور کنید.

## معیار بازگشت فوری

در هرکدام از شرایط زیر، انتشار را متوقف و rollback کنید:

- health check ناموفق است یا سرویس پس از ۱۵ ثانیه آماده نمی‌شود؛
- خطای 5xx بیش از ۲٪ برای پنج دقیقه دیده شود؛
- ثبت‌نام/OTP، ثبت رسید پرداخت یا فعال‌سازی آزمون از کار افتاده باشد؛
- دادهٔ مشتری به‌اشتباه نمایش داده شود یا مجوز حساس نادرست عمل کند.

## بازگشت کد

ابتدا commit سالم قبلی را از `release-history.log` یا Git مشخص کنید. rollback کد، داده را restore نمی‌کند:

```bash
sudo git -c safe.directory=/srv/arvion -C /srv/arvion reset --hard COMMIT_SHA
sudo /srv/arvion/ops/release.sh
curl -fsS https://rvionai.com/health/
```

اگر migration ناسازگار یا داده آسیب‌دیده است، پیش از هر restore با مالک سیستم هماهنگ کنید. از `pre-release-*.dump` مربوط به همان انتشار استفاده کنید؛ restore پایگاه‌داده production عملیاتی مخرب است و نباید خودکار یا بدون تأیید انجام شود.

## پشتیبان و سلامت دوره‌ای

- PostgreSQL و media روزانه در سرور نگه‌داری می‌شوند و نسخه‌های روزانهٔ قدیمی‌تر از ۳۰ روز حذف می‌شوند.
- restore drill ماهانه روی دیتابیس موقت اجرا می‌شود و دیتابیس اصلی را تغییر نمی‌دهد.
- کنترل سلامت هر ۱۵ دقیقه PostgreSQL، دیسک و تازگی backup را بررسی می‌کند؛ پرداخت فوری SMS می‌گیرد و موارد عادی در Inbox/Push مدیریت می‌شوند.
- تا زمان تعیین Object Storage آروان، backup خارج از سرور وجود ندارد؛ این یک ریسک پذیرفته‌شده و تصمیم باز مالک است.
