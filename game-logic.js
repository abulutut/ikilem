const Ikilem = (() => {
  const TR_ABC = "abcçdefgğhıijklmnoöprsştuüvyz";

  let SOZLUK = [];              // gecerli-tahminler.json — Türkçe alfabetik sıralı
  let SOZLUK_INDEKS = new Map(); // kelime → indeks
  let COZUMLER = [];            // cozumler.json — karışık sıra, günlük seçim için

  // --- Türkçe yardımcılar ---

  function trKucult(str) {
    return str.toLocaleLowerCase("tr");
  }

  // --- Sözlük sorguları ---

  function sozlukteMi(kelime) {
    return SOZLUK_INDEKS.has(trKucult(kelime));
  }

  function sozlukIndeksi(kelime) {
    return SOZLUK_INDEKS.get(trKucult(kelime));
  }

  function kelimeAt(idx) {
    return SOZLUK[idx];
  }

  function sozlukBoyutu() {
    return SOZLUK.length;
  }

  // --- Oyun mantığı ---

  // Tahmin indeksi sıkı eşitsizlikle sınırlar arasında mı?
  function aralikta(tahminIdx, altIdx, ustIdx) {
    return tahminIdx > altIdx && tahminIdx < ustIdx;
  }

  // Tahmin cevaba göre hangi sınırı güncellemeli?
  // Dönüş: 'dogru' | 'alt' | 'ust'
  function sinirKarari(tahminIdx, cevapIdx) {
    if (tahminIdx === cevapIdx) return "dogru";
    return tahminIdx < cevapIdx ? "alt" : "ust";
  }

  // Aralık içinden rasgele bir sözlük indeksi döndürür.
  // Aralık boşsa null döner.
  function rastgeleIpucu(altIdx, ustIdx) {
    const min = altIdx + 1;
    const max = ustIdx - 1;
    if (min > max) return null;
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  // --- Tarih / günlük kelime ---

  function bugunTR() {
    const now = new Date(Date.now() + 3 * 60 * 60 * 1000);
    return now.toISOString().slice(0, 10);
  }

  function gunIndeksi(tarih = bugunTR()) {
    const baz = new Date("2025-01-01T00:00:00Z");
    const gun = new Date(tarih + "T00:00:00Z");
    return Math.floor((gun - baz) / 86_400_000);
  }

  function gunKelimesi(tarih) {
    if (!COZUMLER.length) throw new Error("gunKelimesi: yukle() henüz çağrılmadı");
    return COZUMLER[gunIndeksi(tarih) % COZUMLER.length];
  }

  function gunCevapIndeksi(tarih) {
    return sozlukIndeksi(gunKelimesi(tarih));
  }

  // --- Yükleme ---

  async function yukle(baseUrl = ".") {
    const [cozumler, kelimeler] = await Promise.all([
      fetch(`${baseUrl}/cozumler.json`).then(r => r.json()),
      fetch(`${baseUrl}/gecerli-tahminler.json`).then(r => r.json()),
    ]);

    COZUMLER = cozumler;
    SOZLUK = kelimeler;
    SOZLUK_INDEKS = new Map(kelimeler.map((k, i) => [k, i]));

    console.debug(
      `İkilem yüklendi: ${COZUMLER.length} çözüm, ${SOZLUK.length} geçerli tahmin`
    );
    return { cozumSayisi: COZUMLER.length, sozlukBoyutu: SOZLUK.length };
  }

  return {
    yukle,
    sozlukteMi,
    sozlukIndeksi,
    kelimeAt,
    sozlukBoyutu,
    aralikta,
    sinirKarari,
    rastgeleIpucu,
    gunKelimesi,
    gunCevapIndeksi,
    trKucult,
    bugunTR,
    gunIndeksi,
  };
})();

if (typeof window !== "undefined") window.Ikilem = Ikilem;
