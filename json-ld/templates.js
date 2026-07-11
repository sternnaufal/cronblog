/**
 * ============================================================
 * JSON-LD Structured Data Templates
 * Semua subdomain Naufal Rakha Putra
 * 
 * Cara pakai: Copy-paste ke <head> template Blogger/HTML
 * Ganti variabel [BRACKET] sesuai kebutuhan
 * ============================================================
 */

// ============================================================
// 1. blog.naufalrakha.my.id (Penting Literasi) - BlogPosting
// ============================================================
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "[JUDUL_ARTIKEL]",
  "alternativeHeadline": "[SUBTITLE_JIKA_ADA]",
  "image": "[URL_GAMBAR_UTAMA]",
  "author": {
    "@type": "Person",
    "name": "Naufal Rakha Putra",
    "url": "https://naufalrakha.my.id",
    "sameAs": [
      "https://github.com/sternnaufal",
      "https://twitter.com/naufalrakha"
    ]
  },
  "publisher": {
    "@type": "Organization",
    "name": "Penting Literasi",
    "logo": {
      "@type": "ImageObject",
      "url": "https://blog.naufalrakha.my.id/favicon.ico"
    }
  },
  "datePublished": "[TANGGAL_PUBLISH_ISO8601]",
  "dateModified": "[TANGGAL_UPDATE_ISO8601]",
  "description": "[META_DESCRIPTION_MAX_160_CHAR]",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "[URL_ARTIKEL_LENGKAP]"
  },
  "keywords": "[KEYWORD1, KEYWORD2, KEYWORD3]"
}

// ============================================================
// 2. digital.naufalrakha.my.id (Portfolio/Digital) - WebSite + Person
// ============================================================
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Naufal Rakha Putra - Digital Portfolio",
  "url": "https://digital.naufalrakha.my.id/",
  "description": "Portfolio digital Naufal Rakha Putra - Web Developer, Blogger, Tech Enthusiast",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://digital.naufalrakha.my.id/search?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}

{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Naufal Rakha Putra",
  "url": "https://naufalrakha.my.id",
  "sameAs": [
    "https://github.com/sternnaufal",
    "https://twitter.com/naufalrakha",
    "https://linkedin.com/in/naufalrakha",
    "https://blog.naufalrakha.my.id"
  ],
  "jobTitle": "Web Developer & Tech Blogger",
  "worksFor": {
    "@type": "Organization",
    "name": "Freelance"
  },
  "knowsAbout": [
    "Web Development",
    "JavaScript",
    "Python",
    "Blogger",
    "SEO",
    "Content Writing"
  ]
}

// ============================================================
// 3. naufalrakha.my.id (Main Domain) - Person + Organization
// ============================================================
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Naufal Rakha Putra",
  "url": "https://naufalrakha.my.id",
  "description": "Web Developer, Tech Blogger, Content Creator. Penulis blog Penting Literasi.",
  "sameAs": [
    "https://github.com/sternnaufal",
    "https://twitter.com/naufalrakha",
    "https://linkedin.com/in/naufalrakha",
    "https://blog.naufalrakha.my.id",
    "https://digital.naufalrakha.my.id"
  ],
  "jobTitle": "Web Developer & Tech Blogger",
  "knowsAbout": [
    "Web Development",
    "JavaScript",
    "Python",
    "Blogger Platform",
    "SEO",
    "Technical Writing",
    "Content Marketing"
  ],
  "alumniOf": {
    "@type": "EducationalOrganization",
    "name": "[UNIVERSITAS/JURUSAN]"
  }
}

// ============================================================
// 4. sternnaufal.github.io (GitHub Pages) - WebSite + Project
// ============================================================
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "SternNaufal GitHub Pages",
  "url": "https://sternnaufal.github.io/",
  "description": "GitHub Pages repository untuk project-project open source",
  "publisher": {
    "@type": "Person",
    "name": "Naufal Rakha Putra"
  }
}

// ============================================================
// 5. koleksi_naufal (Koleksi ROMs/Games) - ItemList
// ============================================================
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Koleksi ROMs & Games - Naufal Rakha Putra",
  "description": "Kumpulan ROM emulator, game retro, dan koleksi digital",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "SoftwareApplication",
        "name": "[NAMA_GAME_1]",
        "applicationCategory": "Game",
        "operatingSystem": "[PLATFORM]"
      }
    },
    {
      "@type": "ListItem",
      "position": 2,
      "item": {
        "@type": "SoftwareApplication",
        "name": "[NAMA_GAME_2]",
        "applicationCategory": "Game",
        "operatingSystem": "[PLATFORM]"
      }
    }
  ]
}

// ============================================================
// 5. UNIVERSAL - Organization (pasang di semua domain)
// ============================================================
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Naufal Rakha Putra Digital",
  "url": "https://naufalrakha.my.id",
  "logo": "https://naufalrakha.my.id/logo.png",
  "sameAs": [
    "https://github.com/sternnaufal",
    "https://twitter.com/naufalrakha",
    "https://linkedin.com/in/naufalrakha",
    "https://blog.naufalrakha.my.id",
    "https://digital.naufalrakha.my.id"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+62-838-4515-8177",
    "contactType": "customer service",
    "availableLanguage": ["Indonesian", "English"]
  }
}