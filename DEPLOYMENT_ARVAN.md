# استقرار Rvion روی آروان‌کلاد

## اندازه پیشنهادی

برای شروع production با PostgreSQL جدا، ابرک Linux در ایران مرکزی با **۲ vCPU، رم ۴ GB و حداقل دیسک ۵۰ تا ۷۵ GB SSD** مناسب است. نزدیک‌ترین بسته‌های اعلام‌شده آروان `std-small2` با ۲ CPU، رم ۴ GB و دیسک ۷۵ GB یا خانواده `c*-medium1` با ۲ CPU، رم ۴ GB و دیسک ۲۵ GB هستند؛ برای دومی باید Block Storage اضافه شود.

اگر PostgreSQL را نیز روی همان ماشین اجرا می‌کنید، از **۴ vCPU، رم ۸ تا ۱۲ GB و دیسک ۷۵ GB** شروع کنید. برای production ترجیح معماری، دیتابیس ابری/ماشین جدا با backup روزانه و آزمون restore است. فایل‌های رسانه در Object Storage قرار می‌گیرند و static با Nginx/WhiteNoise ارائه می‌شود.

## اجرای یک‌مرحله‌ای

1. Ubuntu 24.04 LTS بسازید، source را در `/srv/arvion` قرار دهید و `.env.production` را از `.env.example` بسازید.
2. PostgreSQL، SMTP و Object Storage را بسازید و تمام placeholderها را پر کنید.
3. اجرا کنید: `sudo /srv/arvion/ops/bootstrap-ubuntu.sh`
4. DNS/CDN و TLS آروان را فعال کنید و `/health/` را از اینترنت بررسی کنید.

اسکریپت idempotent وابستگی سیستم و Python را نصب، migration و داده اولیه/نقش‌ها را اجرا، static را جمع، Gunicorn و Nginx را فعال و health check محلی را کنترل می‌کند. timer روزانه نیز شناسه‌های منقضی مانیتورینگ را پاک می‌کند.

## پشتیبان و rollback

- پیش از هر انتشار از PostgreSQL snapshot/backup بگیرید و restore را دوره‌ای امتحان کنید.
- کد نسخه قبلی را در مسیر release جدا نگه دارید؛ rollback کد یعنی بازگرداندن symlink/source به نسخه قبلی و restart سرویس.
- migration برگشت‌ناپذیر را خودکار reverse نکنید؛ در خطای migration، ترافیک را قطع و از backup آزموده‌شده restore کنید.
- trigger بازگشت: خرابی health، خطای 5xx بیشتر از ۲٪ برای ۵ دقیقه، یا شکست ثبت‌نام/ثبت پرداخت/فعال‌سازی آزمون.

## پس از استقرار

`systemctl status arvion nginx arvion-traffic-cleanup.timer`، سپس ثبت‌نام، ارسال ایمیل، سفارش کارت‌به‌کارت، تأیید ادمین و شروع آزمون را در staging آزمایش کنید. برای خطا و latency زیرساخت نیز سرویس لاگ/مانیتورینگ بیرونی آروان یا ابزار مشابه لازم است؛ آمار داخلی پروژه جای alert زیرساخت را نمی‌گیرد.
