# JSON-LD Install Guide - Semua Subdomain Naufal Rakha Putra

Copy-paste JSON-LD ke `<head>` di setiap domain. Semua tipe ada di `templates.js`.

## Cara Pasang

### Blogger (blog.naufalrakha.my.id)

⚠️ **PENTING:** Hanya JSON-LD **statis** (WebSite, Person, Organization) yang boleh di `<head>`. JSON-LD **dinamis** (BlogPosting, BreadcrumbList) yang pake `<data:post.title/>` dkk. WAJIB di dalem `<b:includable id='post' var='post'>` — kalo ditaruh di `<head>` bakal error `<!--Can't find substitution for tag...-->`.

1. Buka **Blogger Dashboard** → **Theme** → **Edit HTML**
2. Untuk schema **statis** (Person, WebSite, Organization, BreadcrumbList):
   - Cari tag `<head>`, tambah **tepat setelah** `<head>`:
   ```html
   <head>
     <!-- JSON-LD Structured Data -->
     <script type="application/ld+json">
     {
       "@context": "https://schema.org",
       "@type": "WebSite",
       "name": "Penting Literasi",
       "url": "https://blog.naufalrakha.my.id/"
     }
     </script>
     
     <!-- Person Schema (copy dari templates.js) -->
     <script type="application/ld+json">
     { "copy dari templates.js bagian Person" }
     </script>
     ...
   </head>
   ```
3. Untuk schema **dinamis** (BlogPosting):
   - Cari `<b:includable id='post' var='post'>` di template
   - Tambah script JSON-LD **di DALEM** includable tsb. (bukan di `<head>`!)
   - Lihat `BLOGGER_TEMPLATE_GUIDE.md` bagian 1.B untuk detail.

---

## Per Domain

| Domain | Template | Keterangan |
|--------|----------|------------|
| **naufalrakha.my.id** | Person + Organization | Main domain, profile utama |
| **blog.naufalrakha.my.id** | WebSite + BlogPosting | Blog Penting Literasi |
| **digital.naufalrakha.my.id** | WebSite + Person | Digital portfolio |
| **sternnaufal.github.io** | WebSite | GitHub Pages |
| **koleksi_naufal** | ItemList | Koleksi ROMs |

---

## Template by Domain

### 1. naufalrakha.my.id (Main Domain)
Pasang: **Person** + **Organization** + **WebSite**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Naufal Rakha Putra",
  "url": "https://naufalrakha.my.id",
  "description": "Web Developer, Tech Blogger, Content Creator.",
  "sameAs": [
    "https://github.com/sternnaufal",
    "https://twitter.com/naufalrakha",
    "https://linkedin.com/in/naufalrakha",
    "https://blog.naufalrakha.my.id",
    "https://digital.naufalrakha.my.id"
  ],
  "jobTitle": "Web Developer & Tech Blogger",
  "knowsAbout": ["Web Development", "JavaScript", "Python", "SEO"]
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Naufal Rakha Putra Digital",
  "url": "https://naufalrakha.my.id",
  "logo": "https://naufalrakha.my.id/logo.png",
  "sameAs": [
    "https://github.com/sternnaufal",
    "https://blog.naufalrakha.my.id"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+62-838-4515-8177",
    "contactType": "customer service"
  }
}
</script>
```

### 2. blog.naufalrakha.my.id (Penting Literasi)
Pasang: **WebSite** + **Person**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Penting Literasi",
  "url": "https://blog.naufalrakha.my.id/"
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Naufal Rakha Putra",
  "url": "https://naufalrakha.my.id",
  "sameAs": [
    "https://github.com/sternnaufal",
    "https://twitter.com/naufalrakha"
  ],
  "jobTitle": "Web Developer & Tech Blogger"
}
</script>
```

### 3. digital.naufalrakha.my.id (Portfolio)
Pasang: **WebSite** + **Person**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Naufal Rakha Putra - Digital Portfolio",
  "url": "https://digital.naufalrakha.my.id/",
  "description": "Portfolio digital Naufal Rakha Putra"
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Naufal Rakha Putra",
  "url": "https://naufalrakha.my.id",
  "jobTitle": "Web Developer & Tech Blogger",
  "knowsAbout": ["Web Development", "JavaScript", "Python", "SEO", "Blogger"]
}
</script>
```

### 4. sternnaufal.github.io (GitHub Pages)
Pasang: **WebSite** + **Person**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "SternNaufal GitHub Pages",
  "url": "https://sternnaufal.github.io/",
  "publisher": {
    "@type": "Person",
    "name": "Naufal Rakha Putra"
  }
}
</script>
```

### 5. Koleksi ROMs
Pasang: **ItemList**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Koleksi ROMs & Games - Naufal Rakha Putra",
  "description": "Kumpulan ROM emulator dan game retro"
}
</script>
```

---

## Validate

Setelah pasang, validasi di:
- https://search.google.com/test/rich-results
- https://validator.schema.org/

---

## Checklist

| Domain | JSON-LD | Status |
|--------|---------|--------|
| naufalrakha.my.id | Person + WebSite (index.html) + Organization | ✅ |
| blog.naufalrakha.my.id | WebSite + Person + BlogPosting* | ✅* |
| digital.naufalrakha.my.id | WebSite + Person | ⬜ |
| sternnaufal.github.io | WebSite (via naufalrakha.my.id) | ✅ |
| koleksi_naufal | ItemList | ⬜ |

⚠️ *BlogPosting di blog.naufalrakha.my.id masih broken — schema ada di `<head>` (salah), harus dipindah ke dalem `<b:includable id='post'>`. Lihat `BLOGGER_TEMPLATE_GUIDE.md` bagian 1.B.
