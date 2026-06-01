const NeoQR = {
  async render(container, url) {
    container.innerHTML = "";
    const size = 180;
    if (typeof QRCode !== "undefined") {
      new QRCode(container, {
        text: url,
        width: size,
        height: size,
        colorDark: "#0f172a",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.H,
      });
      return;
    }
    const img = document.createElement("img");
    img.width = size;
    img.height = size;
    img.alt = "QR Code";
    img.src = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(url)}`;
    container.appendChild(img);
  },
};

window.NeoQR = NeoQR;
