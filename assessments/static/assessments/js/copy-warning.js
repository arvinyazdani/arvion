/* Shared question/review policy. Browser events are evidence, not proof of cheating. */
(() => {
  const panel = document.querySelector('[data-copy-warning]');
  const shell = document.querySelector('[data-integrity-url]');
  if (!panel || !shell) return;
  const fa = panel.dataset.lang === 'fa';
  const message = panel.querySelector('[data-copy-message]');
  const counter = panel.querySelector('[data-copy-counter]');
  const dismiss = panel.querySelector('[data-copy-dismiss]');
  const csrf = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  if (!csrf) return; // Incomplete question snapshots have no answer form.
  let count = Number(panel.dataset.count) || 0;
  let pending = Promise.resolve();
  let stopped = false;
  const limitEnabled = panel.dataset.limitEnabled === 'true';
  const digits = n => fa ? String(n).replace(/[0-9]/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]) : String(n);
  const render = n => {
    count = Math.max(count, n);
    counter.textContent = (fa ? 'تلاش‌های ثبت‌شده: ' : 'Recorded copy attempts: ') + digits(count)
      + (limitEnabled ? (fa ? ' از ۵' : ' of 5') : '');
    panel.dataset.stage = String(Math.min(count, 5));
    if (count >= 4) {
      message.textContent = limitEnabled
        ? (fa ? 'اخطار نهایی: با تلاش پنجم، همین آزمون هدیه متوقف می‌شود. مستقل ادامه دهید.'
              : 'Final warning: the fifth copy attempt stops this welcome assessment. Continue independently.')
        : fa ? 'اخطار جدی: تلاش‌های کپی تکرار شده است. بدون کپی یا کمک بیرونی ادامه دهید.'
        : 'Serious warning: repeated copy attempts. Continue without copying or outside help.';
    }
  };
  render(count);
  dismiss.addEventListener('click', () => { dismiss.hidden = true; });
  // Only an actual selection intersecting protected question text is eligible.
  document.addEventListener('copy', event => {
    if (!event.isTrusted) return;
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    const content = [...document.querySelectorAll('[data-copy-question]')]
      .find(node => range.intersectsNode(node));
    if (!content) return;
    event.preventDefault();
    dismiss.hidden = false;
    message.textContent = fa
      ? 'کپی محتوای آزمون مجاز نیست. این رفتار ثبت می‌شود؛ لطفاً مستقل پاسخ دهید.'
      : 'Copying exam content is not allowed. This action is recorded; answer independently.';
    const eventId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const body = new URLSearchParams({event_type: 'copy', copy_scope: 'question',
      copy_event_id: eventId, item_id: content.dataset.copyQuestion,
      connection_state: navigator.onLine ? 'online' : 'offline'});
    // One retry uses the same identifier; failed requests never inflate the UI count.
    const send = async () => {
      if (stopped) return;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 6000);
      try {
        const response = await fetch(shell.dataset.integrityUrl, {method: 'POST', keepalive: true,
          headers: {'X-CSRFToken': csrf}, body, signal: controller.signal});
        const data = await response.json();
        if (data.stopped && data.stop_url) {
          stopped = true;
          window.location.assign(data.stop_url);
          return;
        }
        if (!response.ok) throw new Error('copy_event_failed');
        render(data.copy_count);
        if (count < 4) message.textContent = fa ? 'تلاش برای کپی ثبت شد. کپی سؤال و گزینه‌ها مجاز نیست؛ مستقل پاسخ دهید.'
                : 'A copy attempt was recorded. Do not copy questions or choices; answer independently.';
        const score = document.getElementById('integrity-status');
        if (score) score.textContent = (fa ? 'سلامت آزمون ' : 'Integrity ') + digits(data.integrity_score) + '%';
      } finally { clearTimeout(timeout); }
    };
    pending = pending.then(() => send().catch(() => send())).catch(() => {
      message.textContent = fa ? 'کپی مجاز نیست. ثبت رخداد تأیید نشد؛ اتصال را بررسی کنید.'
        : 'Copying is not allowed. Recording was not confirmed; check your connection.';
    });
  });
})();
