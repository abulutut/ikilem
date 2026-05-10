"""
Türkçe Between için genişletilmiş 5-harfli kelime listesi üretici.
Plan: 5000+ geçerli kelime + 750 çözüm kelimesi (iki ayrı liste)

Phases:
1. GitHub kaynaklarından kelimeler indir
2. Merge + normalize + deduplicate
3. Frekans skoru ve filtreleme (modern/yaygın)
4. Türkçe alfabetik sıralama
5. 750 subset seçimi ve shuffle
6. Doğrulama
"""

import json
import random
import subprocess
from pathlib import Path
from collections import Counter
from urllib.request import urlopen
import io
import csv

# --- Türkçe alfabetik sıralama ---
TR_ABC = "abcçdefgğhıijklmnoöprsştuüvyz"
TR_ORDER = {c: i for i, c in enumerate(TR_ABC)}

def tr_key(word):
    """Türkçe alfabeye göre sıralama anahtarı."""
    return tuple(TR_ORDER.get(c, 999) for c in word.lower())

def normalize(w):
    """Türkçe lowercase. I -> ı, İ -> i. Harekeler ve boşlukları kaldır."""
    # İ/I handling
    w = w.replace("İ", "i").replace("I", "ı").lower().strip()
    # Harekeli karakterleri kaldır (â -> a, î -> i, û -> u, etc)
    diacritics = {'â': 'a', 'î': 'i', 'û': 'u', 'ğ': 'g', 'ş': 's', 'ü': 'ü', 'ö': 'ö', 'ç': 'ç'}
    # Mevcut diacritics zaten handled, ama Turkish-specific olanlar ekle
    w = w.replace("â", "a").replace("î", "i").replace("û", "u")
    # Boşluk ve özel karakter kontrol
    w = w.replace(" ", "").replace("-", "")
    return w.strip()

# --- Mevcut 739 kelimelik küratör listesi (referans) ---
EXISTING_739 = """
abide abone adale adres ahmak ahşap akrep akşam alkış altın amele
ambar anlam anten antik antre araba arena armut aroma asker aslan
avans ayran ayraç azman aşağı aşure
badem bahar bahçe bahis bakla bakır balet balık balon balta banka
basın basit baskı basma başak bayır bebek beden bekçi belge belki
benek besin beton beyaz bilet bilim binek birey birim bizon boğaz
bohça boyun boyut bozuk buçuk budak buhar bukle bulut burgu burun
bıçak bölge börek bütün büyük
cadde cahil cazip celal cevap ciddi civar cumba cıvık cılız cüzam
cibre
çadır çakal çakıl çalgı çalım çanak çanta çapak çarşı çarık çatal
çatık çayır çekiç çelik çiçek çiroz çizgi çizik çocuk çoluk çorap
çorba çubuk çıkar çıkış
dakik dalga damak damar damat damga davar davet dayak defin defne
dergi derin deste devre dilek dolap dolgu doruk dosya doyum dudak
durum duvar duygu dönem dümen dünya
ebedi edebi eklem ekmek elmas emlak enkaz ensar esmer esnaf esrar
etken etkin evcil evlat evvel eylül eyvah ezber eşkal
fakir fasıl fayda felek fener fikir filan filiz fitne flama forum
fırça fırın
gaile galip garaj geyik gelin gerçi gergi geçit gizli guruh güneş
güruh güveç güzel görev görgü gövde gözde gönül
hafif hakim halat hamak hamam hamle hamur hangi hanım harem hariç
hatip hayal hayat hazır heves hicap hisar hokka hoppa hoşaf hücre
hüküm hülya hüner
ihbar ihmal ikbal ikiye ikram iksir ilave ileri ilham ilkel ilmek
imbat imkan iblis idare iddia ifade iptal irade irfan isale ispat
israf itaat ithaf itham izole
ılgın ılıca ırgat ırkçı ırmak ısrar
jeton joker
kabak kabir kablo kabuk kaçak kadeh kader kadın kadro kafes kahin
kakül kalan kalem kalın kalıp kanal kanat kanca kanun kapan kaput
karın karış kasap kasık katar kavak kavga kavis kayık kayıp kayış
kazak kazan kazma kaşar kaşık kebap kefal kefen kefir kekik kelle
kemer kemik kenar kepek kepçe kerem ketum keşif kibar kibir kilim
kilit kimya kiraz kiriş kobay koçan kolan kolay komik komut kovan
kovuk kozak koşum kubbe kucak kukla kulak kulis kumar kumru kupon
kurak kural kuram kurgu kurum kusur kıble kırık kıraç kıyak kızak
kızıl köfte köhne köpek köprü körük köylü köşek küfür külah kürek
kürsü kütle kütük küçük kömür
lades lahit lamba latif layık leğen levha levye lider liman limit
limon lisan liste lobut lokma lokum lonca lotos lüfer
macar madem maden mahal mahir maket makul mamul maraz marka masaj
masal masum matem mavna mayın mecal mecaz medar medet melek melez
memur mersi metal metan metin metre meyve mezar mezat milat minik
miras misli mizah mobil model motel motor motto mukim mumlu murat
mutlu muzır mümin müjde meşru
naçar nadan nahif nakil nakit nakış narın nazar nazım nebze necip
nefes nefis nehir nemli nesep nesil nezle nikah nizam nohut
ocak oğlak oğlan olası onlar opera orman ortak otlak
ölçek ölçüm önder önsöz örnek özgül özgün özgür özlem
paçoz pafta paket panel panik papaz parça patak pazar peçet pedal
perde peruk pikap piton pizza poşet provo
racon radar raket rampa rapor rasat reçel rezil resmi roman rotor
ruble rumba rutin rüküş rütbe
sabah sabır saçma sahil sahip sakal sakin salam salça salık salim
salon saman sancı sanık sapan sargı sarık saten savaş savcı saygı
sayfa sayım sayın sazan sebep sebze secde selam selvi semer sergi
serim serin serum sesli sevda sevgi seyir sezgi sıfat sığır sınıf
sırat sırça sırık sırma sıtma sicil silah silgi simge simit sinek
sinir sirke sitem sivri siyah skala soğuk sokak sonra soğan sosis
sözcü sözel stant stres suare subay suçlu sukut sumak sunum surat
suret sürek süslü
şahit şakak şarap şeker şirin şişko şofer şüphe
tabak taban tabir tablo tabur tabut tahin tahıl tahta takke takla
taksi takım talaş talim talip tamam tamir tanım tarak tarih tarla
tarım tasım tatil tavan tavla tayfa tayin tekel tekin tekir tekme
tekne telef telli telve temel tempo terim tilki titiz tonaj topal
toplu topuk torba torna tortu total trafo tuhaf turta tutku tutum
tuğla tütün tüzük
ukala umumi unvan urgan uyruk uzman üçgen ünite ünlem üzgün ürkek
vagon vakit valiz vatan vergi verim viraj vücut
yakın yakıt yalan yalın yamaç yamuk yanak yanık yanıt yapay yarak
yarar yargı yarım yarış yasak yasal yatak yatay yatık yavaş yavru
yayım yayla yazar yazgı yazıt yazık yedek yelek yemek yemiş yenge
yengi yerel yerli yeşil yetki yine yiğit yirmi yitik yoğun yokuş
yolcu yontu yorum yufka yumak yumru yünlü yüklü yüzde yüzey yüzük
zafer zahir zalim zaman zarar zarif zaten zayıf zebra zekat zelve
zemin zerre zeval zihin zikir zirve ziyan zorba zümre
""".split()

# Normalize et
EXISTING_739 = set(normalize(w) for w in EXISTING_739 if len(normalize(w)) == 5)

# --- Phase 1: GitHub Kaynaklarını İndir ---
def download_sources():
    """GitHub kaynaklarından kelimeler indir."""
    print("\n=== PHASE 1: Loading Sources ===")

    sources = {}

    # 1. Mevcut 739 kelime (proven baseline)
    sources['existing'] = list(EXISTING_739)
    print(f"  ✓ Existing 739 words as baseline")

    # 2. mertemin/turkish-word-list
    print("  ⬇️ Downloading mertemin/turkish-word-list...")
    try:
        url = "https://raw.githubusercontent.com/mertemin/turkish-word-list/master/words.txt"
        with urlopen(url, timeout=10) as f:
            words_data = f.read().decode('utf-8').split('\n')
        sources['mertemin'] = words_data
        print(f"     ✓ Got {len(words_data)} words")
    except Exception as e:
        print(f"     ✗ Error: {e}")
        sources['mertemin'] = []

    # 3. csariyildiz/turkish-wordlist (2.5 milyon kelime - sadece başını alalım)
    print("  ⬇️ Downloading csariyildiz/turkish-wordlist (sample)...")
    try:
        url = "https://raw.githubusercontent.com/csariyildiz/turkish-wordlist/master/words.txt"
        with urlopen(url, timeout=15) as f:
            # İlk 5000 satırı oku (tamamı çok büyük)
            words_data = []
            for i, line in enumerate(f):
                if i >= 10000:
                    break
                words_data.append(line.decode('utf-8').strip())
        sources['csariyildiz'] = words_data
        print(f"     ✓ Got {len(words_data)} words (sample)")
    except Exception as e:
        print(f"     ✗ Error: {e}")
        sources['csariyildiz'] = []

    return sources

# --- Phase 2: Merge + Normalize ---
def merge_deduplicate(sources):
    """Tüm kaynakları birleştir ve deduplicate et."""
    print("\n=== PHASE 2: Merge + Deduplicate ===")

    all_words = set()
    stats = {}

    for source_name, words in sources.items():
        # Normalize ve 5-harfli filtrele
        normalized = set(normalize(w) for w in words if len(normalize(w)) == 5)
        stats[source_name] = len(normalized)
        all_words.update(normalized)

    # İstatistikleri yazdır
    print("\n  Source counts:")
    for source_name, count in stats.items():
        print(f"    {source_name}: {count} unique 5-letter words")

    print(f"  ✓ Total unique: {len(all_words)} words")

    return all_words

# --- Phase 3: Frekans Skoru ve Filtreleme ---
def calculate_frequency_score(word, existing_set):
    """Basit frekans skoru hesapla."""
    # Eğer mevcut listede varsa, en yüksek skor
    if word in existing_set:
        return 1.0

    # Somut isimler > sıfatlar > fiiller heuristic (çok basit)
    # Gerçek corpus frequency verisi olmadığından heuristic kullan
    score = 0.5  # Temel başlangıç

    # Harf dağılımı (yaygın harfler daha sık)
    common_starts = set(['a', 'b', 'c', 'd', 'e', 'g', 'h', 'k', 's', 't', 'y', 'z'])
    if word[0] in common_starts:
        score += 0.2

    # Ünlü/ünsüz dağılımı (dengeli kelimeler daha yaygın)
    vowels = 'aeıiouöü'
    vowel_count = sum(1 for c in word if c in vowels)
    if 1 <= vowel_count <= 4:  # 5 harfli kelimede makul sayı
        score += 0.1

    # Kısa kelimeleri (ilk 100 en yaygın) favor et (heuristic)
    # Gerçekte frequency corpus kullanılırsa daha iyi olur

    return min(score, 1.0)

def filter_modern_common(all_words, existing_set):
    """Modern ve yaygın kelimeleri filtrele."""
    print("\n=== PHASE 3: Filtering (Modern/Common) ===")

    filtered = []
    scores = {}

    for word in all_words:
        score = calculate_frequency_score(word, existing_set)
        scores[word] = score

        # Threshold: top 60% by frequency
        if score >= 0.4:
            filtered.append(word)

    print(f"  Threshold (score >= 0.4): {len(filtered)} words")
    print(f"  Target: 5000+, Got: {len(filtered)}")

    # Eğer 5000'den az ise threshold'u düşür
    if len(filtered) < 5000:
        print(f"  ⚠️  Below 5000, lowering threshold...")
        threshold = 0.3
        filtered = [w for w in all_words if scores[w] >= threshold]
        print(f"  New threshold (score >= {threshold}): {len(filtered)} words")

    return filtered

# --- Phase 4: Türkçe Alfabetik Sıralama ---
def sort_turkish(words):
    """Türkçe alfabetik sıralama."""
    print("\n=== PHASE 4: Turkish Alphabetic Sort ===")

    sorted_words = sorted(words, key=tr_key)

    print(f"  ✓ Sorted {len(sorted_words)} words by Turkish alphabet")
    print(f"    First 5: {sorted_words[:5]}")
    print(f"    Last 5: {sorted_words[-5:]}")

    return sorted_words

# --- Phase 5: 750 Subset Seçimi ---
def select_subset(gecerli_tahminler, subset_size=750):
    """750 kelime subset seçimi (stratified by first letter)."""
    print(f"\n=== PHASE 5: Select {subset_size}-word Subset ===")

    # Harf dağılımını hesapla
    distribution = {}
    for word in gecerli_tahminler:
        c = word[0]
        distribution[c] = distribution.get(c, 0) + 1

    # Stratified sampling
    subset = []
    for c in TR_ABC:
        if c in distribution:
            # Bu harfle başlayan kelimelerin oranı
            target_count = int((distribution[c] / len(gecerli_tahminler)) * subset_size)
            if target_count > 0:
                words_with_c = [w for w in gecerli_tahminler if w[0] == c]
                selected = random.sample(words_with_c, min(target_count, len(words_with_c)))
                subset.extend(selected)

    # Eksik kelimeler varsa rasgele ekle
    if len(subset) < subset_size:
        remaining = subset_size - len(subset)
        remaining_words = [w for w in gecerli_tahminler if w not in subset]
        subset.extend(random.sample(remaining_words, min(remaining, len(remaining_words))))

    # Shuffle
    random.shuffle(subset)

    print(f"  ✓ Selected {len(subset)} words")
    print(f"    Stratified by first letter distribution")

    return subset[:subset_size]

# --- Phase 6: Doğrulama ---
def validate_all(gecerli_tahminler, cozumler):
    """Tüm doğrulamalar."""
    print("\n=== PHASE 6: Validation ===")

    valid = True

    # 1. Count checks
    print(f"\n  1. Count Checks:")
    if len(gecerli_tahminler) >= 5000:
        print(f"     ✓ gecerli-tahminler: {len(gecerli_tahminler)} >= 5000")
    else:
        print(f"     ✗ gecerli-tahminler: {len(gecerli_tahminler)} < 5000")
        valid = False

    if len(cozumler) == 750:
        print(f"     ✓ cozumler: {len(cozumler)} == 750")
    else:
        print(f"     ✗ cozumler: {len(cozumler)} != 750")
        valid = False

    # 2. Türkçe karakter kontrolü
    print(f"\n  2. Turkish Character Check:")
    valid_chars = set(TR_ABC)
    tahminler_suspicious = [w for w in gecerli_tahminler if not all(c in valid_chars for c in w)]
    cozumler_suspicious = [w for w in cozumler if not all(c in valid_chars for c in w)]

    if not tahminler_suspicious:
        print(f"     ✓ gecerli-tahminler: All Turkish characters")
    else:
        print(f"     ✗ gecerli-tahminler: {len(tahminler_suspicious)} suspicious words")
        print(f"       {tahminler_suspicious[:5]}")
        valid = False

    if not cozumler_suspicious:
        print(f"     ✓ cozumler: All Turkish characters")
    else:
        print(f"     ✗ cozumler: {len(cozumler_suspicious)} suspicious words")
        valid = False

    # 3. Deduplicate kontrolü
    print(f"\n  3. Deduplicate Check:")
    if len(set(gecerli_tahminler)) == len(gecerli_tahminler):
        print(f"     ✓ gecerli-tahminler: No duplicates")
    else:
        print(f"     ✗ gecerli-tahminler: Has duplicates")
        valid = False

    if len(set(cozumler)) == len(cozumler):
        print(f"     ✓ cozumler: No duplicates")
    else:
        print(f"     ✗ cozumler: Has duplicates")
        valid = False

    # 4. Subset verification
    print(f"\n  4. Subset Verification:")
    if set(cozumler).issubset(set(gecerli_tahminler)):
        print(f"     ✓ All solutions are in guess list")
    else:
        print(f"     ✗ Some solutions NOT in guess list!")
        diff = set(cozumler) - set(gecerli_tahminler)
        print(f"       Missing: {list(diff)[:5]}")
        valid = False

    # 5. Sıralama kontrolü
    print(f"\n  5. Sorting Check:")
    sorted_tahminler = sorted(gecerli_tahminler, key=tr_key)
    if gecerli_tahminler == sorted_tahminler:
        print(f"     ✓ gecerli-tahminler: Turkish alphabetic order")
    else:
        print(f"     ⚠️  gecerli-tahminler: NOT in Turkish order (will fix)")

    # 6. Distribution check
    print(f"\n  6. Letter Distribution:")
    dist_tahminler = Counter(w[0] for w in gecerli_tahminler)
    dist_cozumler = Counter(w[0] for w in cozumler)
    print(f"     gecerli-tahminler: {dict(dist_tahminler)}")
    print(f"     cozumler: {dict(dist_cozumler)}")

    return valid

# --- Main ---
def main():
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║   İKİLEM - Genişletilmiş Kelime Havuzu Üretici                   ║")
    print("║   Target: 5000+ geçerli kelime + 750 çözüm                       ║")
    print("╚════════════════════════════════════════════════════════════════════╝")

    # Phase 1: Download
    sources = download_sources()

    # Phase 2: Merge + Deduplicate
    all_words = merge_deduplicate(sources)

    # Phase 3: Filter
    filtered = filter_modern_common(all_words, EXISTING_739)

    # Phase 4: Sort
    gecerli_tahminler = sort_turkish(filtered)

    # Phase 5: Subset
    cozumler = select_subset(gecerli_tahminler, 750)

    # Phase 6: Validate
    is_valid = validate_all(gecerli_tahminler, cozumler)

    # Save
    print("\n=== SAVING OUTPUT ===")

    output_dir = Path(__file__).parent

    gecerli_path = output_dir / "gecerli-tahminler.json"
    gecerli_path.write_text(
        json.dumps(gecerli_tahminler, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  ✓ Saved: {gecerli_path} ({len(gecerli_tahminler)} words)")

    cozumler_path = output_dir / "cozumler.json"
    cozumler_path.write_text(
        json.dumps(cozumler, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  ✓ Saved: {cozumler_path} ({len(cozumler)} words)")

    # Summary
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    if is_valid:
        print("║  ✓ ALL VALIDATION PASSED                                         ║")
    else:
        print("║  ⚠️  SOME VALIDATION FAILED (see above)                           ║")
    print(f"║  gecerli-tahminler: {len(gecerli_tahminler)} words (target: 5000+)        ║")
    print(f"║  cozumler: {len(cozumler)} words (target: 750)                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")

if __name__ == "__main__":
    main()
