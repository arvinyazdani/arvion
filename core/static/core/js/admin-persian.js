(() => {
  const translations = new Map(Object.entries({
    "Skip to main content":"رفتن به محتوای اصلی","Welcome,":"خوش آمدید،","View site":"مشاهده سایت",
    "Change password":"تغییر گذرواژه","Log out":"خروج","Home":"خانه","Search":"جست‌وجو",
    "Filter":"فیلتر","Add":"افزودن","Change":"ویرایش","View":"مشاهده","Delete":"حذف",
    "Save":"ذخیره","Save and continue editing":"ذخیره و ادامه ویرایش","Save and add another":"ذخیره و افزودن مورد دیگر",
    "Delete selected":"حذف موارد انتخاب‌شده","Go":"اجرا","Select all":"انتخاب همه","Clear selection":"پاک‌کردن انتخاب",
    "Pending":"در انتظار","Pending review":"در انتظار بررسی","Paid":"پرداخت‌شده","Failed":"ناموفق",
    "Cancelled":"لغوشده","Refunded":"بازپرداخت‌شده","Approved":"تأییدشده","Rejected":"ردشده",
    "Initiated":"آغازشده","Verified":"تأییدشده","Active":"فعال","Draft":"پیش‌نویس","Reviewed":"بازبینی‌شده",
    "Retired":"بایگانی‌شده","Ready":"آماده","In progress":"در حال اجرا","Submitted":"ارسال‌شده",
    "Expired":"منقضی","Completed":"تکمیل‌شده","Invalidated":"باطل‌شده","Open":"باز","Resolved":"حل‌شده"
  }));
  const translate = value => translations.get(value.trim());
  document.querySelectorAll("option,button,a,th,label,caption,h1,h2,h3").forEach(element => {
    if (element.children.length || !element.textContent.trim()) return;
    const replacement = translate(element.textContent);
    if (replacement) element.textContent = replacement;
  });
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach(node => {
    if (node.parentElement?.closest("script,style,code,pre")) return;
    const replacement = translate(node.nodeValue || "");
    if (replacement) node.nodeValue = node.nodeValue.replace(node.nodeValue.trim(), replacement);
  });
})();
