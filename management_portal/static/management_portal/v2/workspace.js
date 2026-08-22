(() => {
  const builder = document.querySelector('[data-question-builder]');
  if (builder) {
    const list = builder.querySelector('[data-question-list]');
    const total = builder.querySelector('[name="questions-TOTAL_FORMS"]');
    const template = builder.querySelector('[data-empty-question]');
    const renumber = () => list.querySelectorAll('[data-question-row]').forEach((row, index) => {
      const number = row.querySelector('[data-row-number]');
      if (number) number.textContent = String(index + 1);
    });
    builder.addEventListener('click', (event) => {
      const add = event.target.closest('[data-add-question]');
      if (add) {
        const index = Number(total.value);
        const html = template.innerHTML.replaceAll('__prefix__', String(index));
        list.insertAdjacentHTML('beforeend', html);
        total.value = String(index + 1);
        renumber();
        list.lastElementChild?.querySelector('input:not([type="hidden"])')?.focus();
        return;
      }
      const remove = event.target.closest('[data-remove-question]');
      if (!remove) return;
      const row = remove.closest('[data-question-row]');
      const deletion = row?.querySelector('input[name$="-DELETE"]');
      if (deletion && row.querySelector('input[name$="-question_key"]')?.value) {
        deletion.checked = true;
        row.hidden = true;
      } else {
        row?.remove();
      }
      renumber();
    });
  }

  const copyButton = document.querySelector('[data-copy-credentials]');
  if (copyButton) copyButton.addEventListener('click', async () => {
    const value = document.querySelector('[data-credentials-text]')?.value || '';
    try {
      await navigator.clipboard.writeText(value.trim());
      copyButton.textContent = document.documentElement.lang === 'fa' ? 'کپی شد ✓' : 'Copied ✓';
    } catch (_) {
      const source = document.querySelector('[data-credentials-text]');
      source?.classList.remove('m-sr-only');
      source?.select();
    }
  });

  const deliveryChoices = document.querySelectorAll('[name="delivery_target"]');
  const recipient = document.querySelector('[data-field="recipient_phone"]');
  const updateRecipient = () => {
    const selected = document.querySelector('[name="delivery_target"]:checked')?.value;
    if (recipient) recipient.hidden = selected !== 'other';
  };
  deliveryChoices.forEach((field) => field.addEventListener('change', updateRecipient));
  updateRecipient();
})();
