#import "@preview/brilliant-cv:4.0.1": *

#let accent = rgb("#2f5d73")
#let muted = rgb("#666666")
#let body-fonts = (
  "Arial",
  "Noto Sans CJK SC",
  "WenQuanYi Micro Hei",
  "Liberation Sans",
)
#let header-font = body-fonts

#let icon(path, fill: accent) = box(
  width: 10pt,
  height: 10pt,
  align(
    center + horizon,
    image(bytes(read(path).replace("path d", "path fill=\"" + fill.to-hex() + "\" d")), height: 9pt),
  ),
)

#let fa-angle-right = icon("icons/fa-angle-right.svg")
#let fa-award = icon("icons/fa-award.svg")
#let fa-building-columns = icon("icons/fa-building-columns.svg")
#let fa-code = icon("icons/fa-code.svg")
#let fa-envelope = icon("icons/fa-envelope.svg")
#let fa-github = icon("icons/fa-github.svg")
#let fa-graduation-cap = icon("icons/fa-graduation-cap.svg")
#let fa-phone = icon("icons/fa-phone.svg")
#let fa-user-badge = fa-award
#let fa-language = fa-code
#let fa-work = icon("icons/fa-work.svg")
#let fa-wrench = icon("icons/fa-wrench.svg")

#let contact-lines(
  email,
  phone,
  political-status,
  english-level,
  location: "",
  compensate-template-indent: false,
) = [
  #if compensate-template-indent [#h(-5pt)]
  #if location != "" [#fa-building-columns #h(5pt)#location]
  #if location != "" and email != "" [ #h-bar() ]
  #if email != "" [#fa-envelope #h(5pt)#link("mailto:" + email)[#email]]
  #if (location != "" or email != "") and phone != "" [ #h-bar() ]
  #if phone != "" [#fa-phone #h(5pt)#link("tel:" + phone.replace(" ", ""))[#phone]]
  #linebreak()
  #if compensate-template-indent [#h(-5pt)]
  #if political-status != "" [#fa-user-badge #h(5pt)#political-status]
  #if political-status != "" and english-level != "" [ #h-bar() ]
  #if english-level != "" [#fa-language #h(5pt)#english-level]
]

#let make-metadata(
  first-name: "",
  last-name: "",
  display-name: none,
  quote: "",
  footer: "Curriculum vitae",
  github: "",
  email: "",
  phone: "",
  political-status: "",
  english-level: "",
  birth-ym: "",
  orcid: "",
  scholar: "",
  location: "",
  section-highlight: "first-letters",
  date-width: "3.25cm",
  font-size: "8.7pt",
  photo-radius: "50%",
  show-online-links: true,
  two-line-contact: false,
) = {
  let info = (:)
  if two-line-contact {
    info.insert("custom-contact-lines", (
      text: contact-lines(
        email,
        phone,
        political-status,
        english-level,
        location: location,
        compensate-template-indent: true,
      ),
      link: "",
    ))
  } else {
    if location != "" {
      info.insert("custom-location", (text: location, link: ""))
    }
    if email != "" {
      info.insert("custom-email", (text: email, link: "mailto:" + email))
    }
    if phone != "" {
      info.insert("custom-phone", (text: phone, link: "tel:" + phone.replace(" ", "")))
    }
    if political-status != "" {
      info.insert("custom-political-status", (text: political-status, link: ""))
    }
    if english-level != "" {
      info.insert("custom-english-level", (text: english-level, link: ""))
    }
    if birth-ym != "" {
      info.insert("custom-birth-ym", (text: birth-ym, link: ""))
    }
  }
  if show-online-links and (github != "" or orcid != "" or scholar != "") {
    info.insert("linebreak", "")
  }
  if show-online-links and github != "" {
    info.insert("custom-github", (text: github, link: github))
  }
  if show-online-links and orcid != "" {
    info.insert("custom-orcid", (text: orcid, link: orcid))
  }
  if show-online-links and scholar != "" {
    info.insert("custom-scholar", (text: scholar, link: scholar))
  }

  (
    header_quote: quote,
    cv_footer: footer,
    layout: (
      awesome_color: "#2f5d73",
      before_section_skip: "0pt",
      before_entry_skip: "1pt",
      before_entry_description_skip: "1pt",
      paper_size: "a4",
      date_width: date-width,
      font_size: font-size,
      fonts: (
        regular_fonts: body-fonts,
        header_font: header-font,
      ),
      header: (
        header_align: "left",
        display_profile_photo: true,
        profile_photo_radius: photo-radius,
        info_font_size: "8.8pt",
      ),
      entry: (
        display_entry_society_first: false,
        display_logo: false,
      ),
      section: (
        title_highlight: section-highlight,
        title_highlight_letters: 3,
      ),
      footer: (
        display_page_counter: true,
        display_footer: true,
      ),
    ),
    personal: (
      first_name: first-name,
      last_name: last-name,
      display_name: display-name,
      info: info,
    ),
  )
}

#let contact-icons = (
  "custom-location": fa-building-columns,
  "custom-email": fa-envelope,
  "custom-phone": fa-phone,
  "custom-political-status": fa-user-badge,
  "custom-english-level": fa-language,
  "custom-birth-ym": fa-user-badge,
  "custom-github": fa-github,
  "custom-orcid": fa-graduation-cap,
  "custom-scholar": fa-code,
)

#let hsep() = h-bar()

#let circle-photo(path, size: 2.75cm) = box(
  width: size,
  height: size,
  radius: 50%,
  clip: true,
  image(path, width: size, height: size, fit: "cover"),
)

#let resume-repeat-header(
  name,
  email,
  phone,
  political-status,
  english-level,
  photo-path,
  location: "",
  subtitle: none,
  name-size: 24pt,
  info-size: 8.65pt,
) = block(below: 8pt)[
  #table(
    columns: (auto, 1fr, 2.75cm),
    inset: 0pt,
    stroke: none,
    column-gutter: 14pt,
    align: horizon,
    text(size: name-size, weight: "bold", fill: rgb("#212529"))[#name],
    [
      #text(size: info-size, fill: accent)[
        #contact-lines(
          email,
          phone,
          political-status,
          english-level,
          location: location,
        )
      ]
      #if subtitle != none [
        #linebreak()
        #text(size: 9pt, fill: accent)[#subtitle]
      ]
    ],
    align(right, circle-photo(photo-path)),
  )
]

#let cv-with-custom-header(metadata, header, doc) = {
  cv-metadata.update(metadata)

  let paper-size = metadata.layout.at("paper_size", default: "a4")
  let font-size = eval(metadata.layout.at("font_size", default: "9pt"))
  let footer-text = metadata.at("cv_footer", default: "")
  let footer-style(body) = text(size: 8pt, fill: rgb("#999999"))[#body]

  set text(
    font: body-fonts,
    weight: "regular",
    size: font-size,
    fill: rgb("#444444"),
  )
  set align(left)
  set page(
    paper: paper-size,
    margin: if paper-size == "us-letter" {
      (left: 2cm, right: 1.4cm, top: 1.2cm, bottom: 1.2cm)
    } else {
      (left: 1.4cm, right: 1.4cm, top: 1cm, bottom: 1cm)
    },
    footer: context table(
      columns: (auto, 1fr, auto),
      inset: -5pt,
      stroke: none,
      footer-style([]),
      align(center, footer-style(footer-text)),
      align(right, footer-style(counter(page).display())),
    ),
  )

  header
  doc
}

#let stable-cv-entry(..args) = block(breakable: false)[
  #cv-entry(..args)
]

#let tags(..items) = items.pos()

#let capsule-tag(content) = box(
  inset: (x: 5pt, y: 1.35pt),
  radius: 7pt,
  stroke: 0.35pt + rgb("#b8ccd6"),
  fill: rgb("#f3f7f9"),
  text(size: 0.86em, fill: accent)[#content],
)

#let capsule-tags(..items) = {
  for pair in items.pos().enumerate() {
    if pair.at(0) > 0 {
      h(3.6pt)
    }
    capsule-tag(pair.at(1))
  }
}

#let metric-pill(content) = box(
  inset: (x: 4pt, y: 1.1pt),
  radius: 3pt,
  stroke: 0.35pt + rgb("#b8ccd6"),
  fill: rgb("#f7fafb"),
  text(size: 0.84em, fill: accent)[#content],
)

#let achievement-entry(
  title: none,
  paper: none,
  metrics: none,
  role: none,
  date: none,
  location: none,
  description: none,
) = stable-cv-entry(
  title: title,
  society: [
    #paper #h(3.5pt)#metric-pill(metrics) #h(3.5pt)#text(fill: muted)[#role]
  ],
  date: date,
  location: location,
  description: description,
)

#let project-entry(
  title: none,
  outcome: none,
  metrics: none,
  role-note: none,
  date: none,
  role: none,
  description: none,
) = stable-cv-entry(
  title: title,
  society: [
    #outcome
    #if metrics != none { [ #h(3.5pt)#metric-pill(metrics)] }
    #if role-note != none { [ #h(3.5pt)#text(fill: muted)[#role-note]] }
  ],
  date: date,
  location: role,
  description: description,
)

#let compact-summary(title, body) = block(below: 3pt)[
  #set par(leading: 0.62em)
  #text(weight: "bold")[#title] #body
]

#let compact-note(body) = block(below: 3pt)[
  #set par(leading: 0.62em)
  #body
]

#let skill-item(label, body, label-width: 3.05cm) = block(below: 6.2pt)[
  #set par(leading: 0.82em, justify: false)
  #table(
    columns: (0.42cm, label-width, 1fr),
    column-gutter: 0pt,
    inset: 0pt,
    stroke: none,
    text(weight: "bold", fill: rgb("#111111"))[•],
    text(weight: "bold", fill: rgb("#111111"))[#label：],
    body,
  )
]

#let inline-authors(authors, self-positions: ()) = [
  #for pair in authors.enumerate() {
    let index = pair.at(0)
    let position = index + 1
    let author = pair.at(1)
    if index > 0 [; ]
    if position in self-positions {
      underline(author)
    } else {
      author
    }
  }
]

#let publication-citation(
  authors,
  title,
  journal,
  year,
  number: none,
  journal-short: none,
  volume: none,
  issue: none,
  pages: none,
  article-number: none,
  doi: none,
  impact: none,
  self-positions: (),
  note: none,
) = {
  let venue = if journal-short != none and journal-short != "" { journal-short } else { journal }
  let pub-year = if year != none and year != "" { year } else { "n.d." }
  let locator = if volume != none and volume != "" {
    [#text(style: "italic")[#volume]#if issue != none and issue != "" [(#issue)]]
  } else {
    none
  }
  let page-range = if pages != none and pages != "" {
    pages
  } else if article-number != none and article-number != "" {
    article-number
  } else {
    none
  }
  let number-width = 1.55em
  let body = [
    #set par(justify: false, leading: 0.66em)
    #inline-authors(authors, self-positions: self-positions) #title. #text(style: "italic")[#venue] #strong(pub-year)#if locator != none [, #locator]#if page-range != none [, #page-range].
    #if doi != none [
      #text(fill: muted)[ DOI: #link("https://doi.org/" + doi)[#("https://doi.org/" + doi)]]
    ]
    #if impact != none [
      #text(fill: muted)[ (#impact)]
    ]
    #if note != none [
      #h(3pt)#text(fill: muted)[(#note)]
    ]
  ]

  block(above: 1pt, below: 5.6pt, inset: (left: 0pt), breakable: true)[
    #if number != none [
      #table(
        columns: (number-width, 1fr),
        column-gutter: 3pt,
        inset: 0pt,
        stroke: none,
        [#number.],
        body,
      )
    ] else [
      #body
    ]
  ]
}

#let publication-summary(label, info) = cv-skill(type: label, info: info)
