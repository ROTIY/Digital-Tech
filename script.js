document.addEventListener('DOMContentLoaded', () => {
  const payButton = document.getElementById('payButton');
  const status = document.getElementById('status');
  const phoneInput = document.getElementById('phone');
  const gamesInput = document.getElementById('games');
  const totalDisplay = document.getElementById('totalDisplay');
  const tableInfo = document.getElementById('tableInfo');
  const tableNumberSpan = document.getElementById('tableNumber');

  const PRICE_PER_GAME = 20;

  
  const urlParams = new URLSearchParams(window.location.search);
  const tableId = urlParams.get('table') || 'Unknown'; 

  
  if (tableId !== 'Unknown') {
    tableNumberSpan.textContent = tableId;
    tableInfo.style.display = 'block';
    document.title = `Pay for ${tableId} | Digital Tech Pool`;
  } else {
    tableInfo.style.display = 'none';
  }

  
  function formatPhone(value) {
    let digits = value.replace(/[^\d+]/g, '');
    if (digits.startsWith('+254')) digits = digits.replace('+254', '0');
    else if (digits.startsWith('254')) digits = digits.replace('254', '0');
    digits = digits.replace(/\D/g, '').substring(0, 10);
    let formatted = '';
    if (digits.length > 0) {
      formatted = digits.startsWith('0') ? '0' : '';
      const rest = digits.substring(formatted ? 1 : 0);
      if (rest.length > 0) formatted += rest.substring(0, 3);
      if (rest.length > 3) formatted += ' ' + rest.substring(3, 6);
      if (rest.length > 6) formatted += ' ' + rest.substring(6, 10);
    }
    return formatted;
  }

  phoneInput.addEventListener('input', (e) => {
    const cursorPos = phoneInput.selectionStart;
    const oldLength = phoneInput.value.length;
    const formatted = formatPhone(e.target.value);
    phoneInput.value = formatted;
    phoneInput.setSelectionRange(cursorPos + (formatted.length - oldLength), cursorPos + (formatted.length - oldLength));
  });

  phoneInput.addEventListener('blur', () => {
    let val = phoneInput.value.replace(/\D/g, '');
    if (val.length === 9 && !val.startsWith('0')) val = '0' + val;
    else if (val.length === 10 && (val.startsWith('7') || val.startsWith('1'))) val = '0' + val;
    phoneInput.value = formatPhone(val);
  });

  
  function updateTotal() {
    let games = parseInt(gamesInput.value) || 1;
    if (games < 1) games = 1;
    const total = games * PRICE_PER_GAME;
    totalDisplay.textContent = `Total: ${total} KSh (${games} game${games !== 1 ? 's' : ''})`;
    payButton.textContent = `Pay ${total} KSh via M-Pesa`;
  }

  gamesInput.addEventListener('input', updateTotal);
  gamesInput.addEventListener('change', updateTotal);
  updateTotal();

  
  payButton.addEventListener('click', async () => {
    let rawPhone = phoneInput.value.replace(/\D/g, '');
    if (rawPhone.startsWith('0')) rawPhone = '254' + rawPhone.substring(1);
    else if (!rawPhone.startsWith('254')) rawPhone = '254' + rawPhone;
    rawPhone = '+' + rawPhone;

    let games = parseInt(gamesInput.value) || 1;
    if (games < 1) games = 1;

    if (rawPhone.length !== 13 || (!rawPhone.startsWith('+2547') && !rawPhone.startsWith('+2541'))) {
      status.textContent = "Please enter a valid Kenyan phone number (e.g. 0712345678)";
      return;
    }

    const amount = games * PRICE_PER_GAME;

    status.textContent = `Requesting payment for ${games} game${games !== 1 ? 's' : ''} on ${tableId}... Check your phone.`;
    payButton.disabled = true;

    try {
      const response = await fetch('https://your-backend-domain.com/api/initiate-stk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: rawPhone,
          amount: amount,
          games: games,
          tableId: tableId  
        })
      });

      const data = await response.json();

      if (data.success || data.ResponseCode === "0") {
        status.textContent = `Payment requested for ${tableId}! Enter PIN on your phone. Balls release soon...`;
      } else {
        status.textContent = "Error: " + (data.message || data.ResultDesc || "Failed");
        payButton.disabled = false;
      }
    } catch (err) {
      status.textContent = "Network error – try again";
      payButton.disabled = false;
      console.error(err);
    }
  });
});