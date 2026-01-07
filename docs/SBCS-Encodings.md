# Single-Byte Character Set (SBCS) Encodings

This document provides a comprehensive reference of all Single-Byte Character Set (SBCS) encodings that can represent languages using 256 characters or less (one byte per character).

## Overview

SBCS encodings are character encodings that use exactly one byte (8 bits) for each graphic character, allowing a maximum of 256 distinct characters (0-255). The first 128 characters (0-127) are typically identical to ASCII, with the upper 128 characters (128-255) containing language-specific characters.

## Windows Code Pages (CP125x Series)

### CP1250 (Windows-1250) - Central European

**Encoding:** `cp1250`, `windows-1250`  
**Languages:** Czech, Polish, Slovak, Hungarian, Slovene, Serbo-Croatian (Latin script), Montenegrin, Romanian (before 1993 spelling reform), Turkmen, Rotokas, Albanian, English, German, Irish, Luxembourgish, Dutch  
**ISO Equivalent:** ISO-8859-2 (with differences)

### CP1251 (Windows-1251) - Cyrillic

**Encoding:** `cp1251`, `windows-1251`  
**Languages:** Russian, Bulgarian, Belarusian, Macedonian, Serbian (Cyrillic), Ukrainian  
**ISO Equivalent:** ISO-8859-5 (with differences)

### CP1252 (Windows-1252) - Western European

**Encoding:** `cp1252`, `windows-1252`  
**Languages:** Albanian, Basque, Breton, Catalan, Danish, Dutch, English, Faroese, Finnish, French, German, Greenlandic, Icelandic, Irish Gaelic, Italian, Latin, Luxemburgish, Norwegian, Portuguese, Rhaeto-Romanic, Scottish Gaelic, Spanish, Swedish, Afrikaans, Swahili, Indonesian  
**ISO Equivalent:** ISO-8859-1 (with differences - uses C1 control area for additional characters)

### CP1253 (Windows-1253) - Greek

**Encoding:** `cp1253`, `windows-1253`  
**Languages:** Greek  
**ISO Equivalent:** ISO-8859-7 (with differences)

### CP1254 (Windows-1254) - Turkish

**Encoding:** `cp1254`, `windows-1254`  
**Languages:** Turkish, Azeri (Latin), Uzbek (Latin)  
**ISO Equivalent:** ISO-8859-9 (with differences)

### CP1255 (Windows-1255) - Hebrew

**Encoding:** `cp1255`, `windows-1255`  
**Languages:** Hebrew  
**ISO Equivalent:** ISO-8859-8 (with differences)

### CP1256 (Windows-1256) - Arabic

**Encoding:** `cp1256`, `windows-1256`  
**Languages:** Arabic, Farsi (Persian), Urdu  
**ISO Equivalent:** ISO-8859-6 (with differences)

### CP1257 (Windows-1257) - Baltic

**Encoding:** `cp1257`, `windows-1257`  
**Languages:** Estonian, Latvian, Lithuanian, Latgalian, Polish, Slovene, Swedish, Finnish, Norwegian, Danish, German, English, Māori, Rotokas, Hawaiian, Niuean, Samoan, Tokelauan, Tongan, Tuvaluan, Hepburn romanization/Japanese transliteration, Persian transliteration  
**ISO Equivalent:** ISO-8859-13 (with differences)

### CP1258 (Windows-1258) - Vietnamese

**Encoding:** `cp1258`, `windows-1258`  
**Languages:** Vietnamese, English, French, German, Spanish, Danish, Norwegian, Swedish, Finnish, Irish, Albanian, Luxembourgish, Dutch. With combining diacritics: Asturian, Estonian, Italian, Portuguese, Guarani, Igbo, Nauruan, Yoruba  
**Note:** Uses combining diacritics for Vietnamese tone marks

### CP874 (Windows-874) - Thai

**Encoding:** `cp874`, `windows-874`, `tis-620`  
**Languages:** Thai  
**ISO Equivalent:** ISO-8859-11 / TIS-620 (with differences)

## ISO/IEC 8859 Series

### ISO-8859-1 (Latin-1) - Western European

**Encoding:** `iso-8859-1`, `latin1`, `l1`  
**Languages:** Afrikaans, Albanian, Basque, Breton, Catalan, Cornish, Danish, Dutch, English, Faroese, Finnish, French, Frisian, Galician, German, Greenlandic, Icelandic, Irish, Italian, Latin, Luxemburgish, Norwegian, Portuguese, Rhaeto-Romanic, Scottish Gaelic, Spanish, Swedish, Swahili, Indonesian  
**Windows Equivalent:** CP1252 (with differences)

### ISO-8859-2 (Latin-2) - Central and Eastern European

**Encoding:** `iso-8859-2`, `latin2`, `l2`  
**Languages:** Bosnian, Croatian, Czech, German, Hungarian, Polish, Romanian (with ş/ţ instead of ș/ț), Slovak, Slovene, Serbian (Latin script)  
**Windows Equivalent:** CP1250 (with differences)

### ISO-8859-3 (Latin-3) - South European

**Encoding:** `iso-8859-3`, `latin3`, `l3`  
**Languages:** Afrikaans, Catalan, Dutch, English, Esperanto, German, Italian, Maltese, Spanish, Turkish  
**Status:** Largely superseded by ISO-8859-9 for Turkish

### ISO-8859-4 (Latin-4) - North European

**Encoding:** `iso-8859-4`, `latin4`, `l4`  
**Languages:** Danish, English, Estonian, Finnish, German, Greenlandic, Latin, Latvian, Lithuanian, Norwegian, Sámi (Lappish), Slovenian, Swedish  
**Status:** Largely superseded by ISO-8859-10 and ISO-8859-13

### ISO-8859-5 (Latin/Cyrillic)

**Encoding:** `iso-8859-5`, `cyrillic`  
**Languages:** Belarusian, Bulgarian, Macedonian, Russian, Serbian (Cyrillic), Ukrainian  
**Windows Equivalent:** CP1251 (with differences)  
**Note:** Less commonly used than KOI8-R or Windows-1251

### ISO-8859-6 (Latin/Arabic)

**Encoding:** `iso-8859-6`, `arabic`  
**Languages:** Arabic  
**Windows Equivalent:** CP1256 (with differences)  
**Note:** Basic Arabic alphabet only, no vowel signs

### ISO-8859-7 (Latin/Greek)

**Encoding:** `iso-8859-7`, `greek`, `greek8`  
**Languages:** Greek  
**Windows Equivalent:** CP1253 (with differences)

### ISO-8859-8 (Latin/Hebrew)

**Encoding:** `iso-8859-8`, `hebrew`  
**Languages:** Hebrew  
**Windows Equivalent:** CP1255 (with differences)  
**Note:** Hebrew letters without vowel signs

### ISO-8859-9 (Latin-5) - Turkish

**Encoding:** `iso-8859-9`, `latin5`, `l5`  
**Languages:** Turkish, Azeri (Latin), Uzbek (Latin)  
**Windows Equivalent:** CP1254 (with differences)  
**Note:** Similar to ISO-8859-1 but replaces Icelandic characters with Turkish ones

### ISO-8859-10 (Latin-6) - Nordic

**Encoding:** `iso-8859-10`, `latin6`, `l6`  
**Languages:** Danish, English, Estonian, Finnish, German, Greenlandic, Icelandic, Latvian, Lithuanian, Norwegian, Sámi (Lappish), Swedish  
**Note:** Rearrangement of Latin-4 to cover entire Nordic area

### ISO-8859-11 (Latin/Thai)

**Encoding:** `iso-8859-11`, `tis-620`  
**Languages:** Thai  
**Windows Equivalent:** CP874 (with differences)  
**Note:** Nearly identical to TIS-620 (Thai Industrial Standard 620-2533)

### ISO-8859-13 (Latin-7) - Baltic Rim

**Encoding:** `iso-8859-13`, `latin7`  
**Languages:** Estonian, Latvian, Lithuanian, Polish  
**Windows Equivalent:** CP1257 (with differences)

### ISO-8859-14 (Latin-8) - Celtic

**Encoding:** `iso-8859-14`, `latin8`, `l8`, `celtic`  
**Languages:** Welsh, Irish Gaelic, Scottish Gaelic, Manx, Cornish, Breton, Old Irish  
**Note:** Covers Celtic languages

### ISO-8859-15 (Latin-9) - Western European (Revised)

**Encoding:** `iso-8859-15`, `latin9`, `l9`  
**Languages:** Same as ISO-8859-1, plus: French, Finnish  
**Note:** Revision of ISO-8859-1 with Euro sign and additional French/Finnish characters

### ISO-8859-16 (Latin-10) - South-Eastern European

**Encoding:** `iso-8859-16`, `latin10`, `l10`  
**Languages:** Albanian, Croatian, Hungarian, Italian, Polish, Romanian, Serbian, Slovenian, plus: Finnish, French, German, Irish Gaelic  
**Note:** Intended for Central, Eastern and Southern European languages

## DOS Code Pages (OEM)

### CP437 - US English

**Encoding:** `cp437`, `ibm437`, `437`  
**Languages:** English, German, Swedish  
**Note:** Original IBM PC code page with box-drawing characters

### CP737 - Greek

**Encoding:** `cp737`, `ibm737`  
**Languages:** Greek  
**Note:** DOS Greek

### CP775 - Baltic

**Encoding:** `cp775`, `ibm775`  
**Languages:** Estonian, Lithuanian, Latvian  
**Note:** DOS Baltic

### CP850 - Multilingual Latin-1

**Encoding:** `cp850`, `ibm850`, `850`  
**Languages:** Danish, Dutch, English, French, German, Icelandic, Italian, Norwegian, Portuguese, Spanish, Swedish  
**Note:** DOS version of Latin-1, retains some box-drawing characters

### CP852 - Central/Eastern European

**Encoding:** `cp852`, `ibm852`, `852`  
**Languages:** Czech, Polish, Slovak, Hungarian, Croatian, Slovene, Romanian  
**Note:** DOS version of Latin-2, different arrangement than ISO-8859-2

### CP855 - Cyrillic

**Encoding:** `cp855`, `ibm855`  
**Languages:** Bulgarian, Belarusian, Macedonian, Russian, Serbian (Cyrillic), Ukrainian  
**Note:** DOS Cyrillic, different arrangement than ISO-8859-5

### CP857 - Turkish

**Encoding:** `cp857`, `ibm857`  
**Languages:** Turkish  
**Note:** DOS Turkish

### CP860 - Portuguese

**Encoding:** `cp860`, `ibm860`  
**Languages:** Portuguese  
**Note:** DOS Portuguese

### CP861 - Icelandic

**Encoding:** `cp861`, `ibm861`  
**Languages:** Icelandic  
**Note:** DOS Icelandic

### CP862 - Hebrew

**Encoding:** `cp862`, `ibm862`  
**Languages:** Hebrew  
**Note:** DOS Hebrew

### CP863 - Canadian French

**Encoding:** `cp863`, `ibm863`  
**Languages:** French (Canadian)  
**Note:** DOS Canadian French

### CP864 - Arabic

**Encoding:** `cp864`, `ibm864`  
**Languages:** Arabic  
**Note:** DOS Arabic

### CP865 - Nordic

**Encoding:** `cp865`, `ibm865`  
**Languages:** Danish, Norwegian  
**Note:** DOS Nordic

### CP866 - Cyrillic (Russian)

**Encoding:** `cp866`, `ibm866`  
**Languages:** Russian, Belarusian, Ukrainian  
**Note:** DOS Russian Cyrillic, most common DOS Cyrillic encoding

### CP869 - Greek

**Encoding:** `cp869`, `ibm869`  
**Languages:** Greek  
**Note:** DOS Modern Greek

## KOI8 Encodings

### KOI8-R - Russian

**Encoding:** `koi8-r`, `cskoi8r`  
**Languages:** Russian, Bulgarian  
**Note:** Most widely used Cyrillic encoding in Unix systems and email

### KOI8-U - Ukrainian

**Encoding:** `koi8-u`  
**Languages:** Ukrainian, Russian, Bulgarian  
**Note:** Based on KOI8-R with Ukrainian-specific characters (Ґ, Є, І, Ї)

### KOI8-RU - Russian/Ukrainian/Belarusian

**Encoding:** `koi8-ru`  
**Languages:** Russian, Ukrainian, Belarusian  
**Note:** Extension of KOI8-U with Belarusian character Ў

## Macintosh Encodings

### MacRoman - Western European

**Encoding:** `mac-roman`, `macintosh`, `x-mac-roman`  
**Languages:** English, French, German, and other Western European languages  
**Note:** Original Macintosh character encoding

### MacCentralEurope - Central European

**Encoding:** `mac-centraleurope`, `mac-latin2`, `x-mac-ce`  
**Languages:** Czech, Slovak, Hungarian, Polish, Estonian, Latvian, Lithuanian  
**Note:** Macintosh Central European

### MacCyrillic - Cyrillic

**Encoding:** `mac-cyrillic`, `x-mac-cyrillic`  
**Languages:** Belarusian, Bulgarian, Macedonian, Russian, Serbian (Cyrillic)  
**Note:** Macintosh Cyrillic

### MacGreek - Greek

**Encoding:** `mac-greek`, `x-mac-greek`  
**Languages:** Greek  
**Note:** Macintosh Greek

### MacHebrew - Hebrew

**Encoding:** `mac-hebrew`, `x-mac-hebrew`  
**Languages:** Hebrew  
**Note:** Macintosh Hebrew

### MacIceland - Icelandic

**Encoding:** `mac-iceland`, `x-mac-iceland`  
**Languages:** Icelandic  
**Note:** Macintosh Icelandic

### MacTurkish - Turkish

**Encoding:** `mac-turkish`, `x-mac-turkish`  
**Languages:** Turkish  
**Note:** Macintosh Turkish

### MacThai - Thai

**Encoding:** `mac-thai`, `x-mac-thai`  
**Languages:** Thai  
**Note:** Macintosh Thai, variant of TIS-620

### MacUkraine - Ukrainian

**Encoding:** `mac-ukraine`, `x-mac-ukraine`  
**Languages:** Ukrainian  
**Note:** Macintosh Ukrainian

### MacCroatian - Croatian

**Encoding:** `mac-croatian`, `x-mac-croatian`  
**Languages:** Croatian  
**Note:** Macintosh Croatian

### MacRomania - Romanian

**Encoding:** `mac-romania`, `x-mac-romania`  
**Languages:** Romanian  
**Note:** Macintosh Romanian

### MacArabic - Arabic

**Encoding:** `mac-arabic`, `x-mac-arabic`  
**Languages:** Arabic  
**Note:** Macintosh Arabic

## Regional and National SBCS Encodings

### ArmSCII-8 - Armenian

**Encoding:** `armscii-8`, `armscii8`  
**Languages:** Armenian  
**Note:** Armenian Standard Code for Information Interchange, 8-bit encoding. Lower 128 characters are ASCII, upper 128 contain Armenian alphabet.

### GEOSTD8 - Georgian

**Encoding:** `geostd8`, `georgian-academy`, `georgian-ps`  
**Languages:** Georgian  
**Note:** Georgian standard single-byte encoding, de-facto standard in Georgia. Developed for Microsoft Windows environments.

### TSCII - Tamil

**Encoding:** `tscii`  
**Languages:** Tamil  
**Note:** Tamil Script Code for Information Interchange. Bilingual 8-bit glyph-based encoding (Roman and Tamil). Lower 128 codepoints are ASCII, upper 128 are TSCII-specific Tamil characters.

### Mazovia - Polish (Regional)

**Encoding:** `mazovia`, `cp667`, `cp790`, `cp991`  
**Languages:** Polish  
**Note:** Character set used under DOS to represent Polish text. Derived from code page 437 with Polish letters. Maintains box-drawing characters from CP437.

### Kamenický - Czech/Slovak (Regional)

**Encoding:** `kamenicky`, `keybcs2`, `cp867`, `cp895`  
**Languages:** Czech, Slovak  
**Note:** Code page for DOS, very popular in Czechoslovakia (1985-1995). Based on CP437 with Czech and Slovak characters replacing similar-looking glyphs.

### VISCII - Vietnamese (Legacy)

**Encoding:** `viscii`  
**Languages:** Vietnamese  
**Note:** Modified ASCII character encoding for Vietnamese. Keeps 95 printable ASCII characters, replaces 6 control characters, adds 128 precomposed Vietnamese characters.

### VSCII (TCVN 5712) - Vietnamese (National Standard)

**Encoding:** `vscii`, `tcvn-5712`, `tcvn3`  
**Languages:** Vietnamese  
**Note:** Vietnamese Standard Code for Information Interchange. Three variants (VSCII-1, VSCII-2, VSCII-3) with different character arrangements.

### VNI - Vietnamese (Legacy)

**Encoding:** `vni`  
**Languages:** Vietnamese  
**Note:** Uses up to two bytes per Vietnamese vowel character (second byte for diacritical marks). More compatible than TCVN3. **Note:** VNI is technically a multi-byte encoding, not a pure SBCS.

### VPS - Vietnamese (Legacy)

**Encoding:** `vps`, `x-viet-vps`  
**Languages:** Vietnamese  
**Note:** VPS (Vietnam Professionals Society) encoding, another legacy Vietnamese encoding variant.

## EBCDIC SBCS Encodings

EBCDIC (Extended Binary Coded Decimal Interchange Code) is an 8-bit character encoding used mainly on IBM mainframe systems. While EBCDIC is primarily for mainframe environments, many EBCDIC code pages are SBCS:

### Common EBCDIC Code Pages

- **CP037** - EBCDIC US-Canada
- **CP273** - EBCDIC Germany/Austria
- **CP277** - EBCDIC Denmark/Norway
- **CP278** - EBCDIC Finland/Sweden
- **CP280** - EBCDIC Italy
- **CP284** - EBCDIC Spain
- **CP285** - EBCDIC UK/Ireland
- **CP297** - EBCDIC France
- **CP420** - EBCDIC Arabic
- **CP424** - EBCDIC Hebrew
- **CP500** - EBCDIC International
- **CP838** - EBCDIC Thai
- **CP870** - EBCDIC Multilingual Latin-2
- **CP871** - EBCDIC Icelandic
- **CP875** - EBCDIC Greek Modern
- **CP1026** - EBCDIC Turkish
- **CP1047** - EBCDIC Latin-1/Open System

**Note:** EBCDIC encodings are primarily used in IBM mainframe environments and are not commonly used in modern desktop applications or games.

## Language Coverage Summary

### Languages with Full SBCS Support

**Western European Languages:**

- English, French, German, Spanish, Italian, Portuguese, Dutch, Danish, Norwegian, Swedish, Finnish, Icelandic, Irish, Scottish Gaelic, Welsh, Breton, Cornish, Manx

**Central/Eastern European Languages:**

- Czech, Slovak, Polish, Hungarian, Romanian, Croatian, Serbian (Latin), Slovenian, Bosnian, Montenegrin

**Cyrillic Languages:**

- Russian, Ukrainian, Belarusian, Bulgarian, Macedonian, Serbian (Cyrillic)

**Other European Languages:**

- Greek, Albanian, Estonian, Latvian, Lithuanian, Turkish, Maltese

**Middle Eastern Languages:**

- Arabic, Hebrew

**Southeast Asian Languages:**

- Thai, Vietnamese

**African Languages:**

- Afrikaans, Swahili

**Other Languages:**

- Esperanto, Latin, Indonesian

**Armenian:**

- Armenian (ArmSCII-8)

**Georgian:**

- Georgian (GEOSTD8)

**Tamil:**

- Tamil (TSCII)

**Additional Latin-Script Languages:**

- Tagalog, Filipino, Hawaiian, Maori, Tahitian, Tongan, Samoan, Fijian, Chamorro, Niuean, Tokelauan, Tuvaluan, Rotokas, Haitian Creole, Hausa (Latin), Javanese (Latin), Sundanese (Latin), Chichewa, Shona, Sotho, Xhosa, Zulu, Walloon, Corsican, Scots, Interlingua, Ido, Rhaeto-Romanic, Romansh, Ladin, Friulian, Latgalian

**Additional Austronesian Languages (Latin Script):**

- Cebuano, Ilocano, Waray, Hiligaynon, Bicol, Kapampangan, Pangasinan, Malagasy, Acehnese, Balinese, Buginese, Madurese, Minangkabau, Batak languages

**Additional African Languages (Latin Script):**

- Twi, Wolof, Kinyarwanda, Luganda, Kikuyu, Sesotho (Southern Sotho), Venda, Tsonga, Bemba, Lingala, Kongo, Fulfulde, Bambara, Malinke, Kirundi, Ndebele, Sango, Ewe, Fon, Akan, Ga, Dagbani, Soninke, Mandinka, Susu, Temne, Mende, Kpelle, Grebo, Vai

**Additional Romance Languages (Latin Script):**

- Sardinian, Sicilian, Neapolitan, Venetian, Lombard, Piedmontese, Ligurian, Emilian-Romagnol, Aragonese, Mirandese, Astur-Leonese, Extremaduran

**Additional Germanic Languages (Latin Script):**

- Low German (Plattdeutsch), Yiddish (Latin script variant), Pennsylvania German, Alemannic, Bavarian, Limburgish

**Additional Slavic Languages (Latin Script):**

- Kashubian, Silesian, Rusyn (Latin variant), Sorbian (Upper and Lower)

**Additional Languages Using Other Scripts (SBCS-Compatible):**

- Pashto (Arabic script - CP1256), Kurdish (Arabic script - CP1256), Sindhi (Arabic script - CP1256), Balochi (Arabic script - CP1256), Uyghur (Arabic script - CP1256), Kazakh (Cyrillic - CP1251), Kyrgyz (Cyrillic - CP1251), Tajik (Cyrillic - CP1251), Mongolian (Cyrillic - CP1251), Ossetian (Cyrillic - CP1251), Tatar (Cyrillic - CP1251), Chuvash (Cyrillic - CP1251), Komi (Cyrillic - CP1251), Mari (Cyrillic - CP1251), Udmurt (Cyrillic - CP1251), Abkhaz (Cyrillic - CP1251), Chechen (Cyrillic - CP1251), Ingush (Cyrillic - CP1251), Avar (Cyrillic - CP1251), Lezgian (Cyrillic - CP1251), Kabardian (Cyrillic - CP1251), Adyghe (Cyrillic - CP1251), Karachay-Balkar (Cyrillic - CP1251), Nogai (Cyrillic - CP1251), Kalmyk (Cyrillic - CP1251), Buryat (Cyrillic - CP1251), Yakut (Cyrillic - CP1251), Tuvan (Cyrillic - CP1251), Khakas (Cyrillic - CP1251), Altai (Cyrillic - CP1251)

**Pacific Languages (Latin Script):**

- Hawaiian, Maori, Tahitian, Tongan, Samoan, Fijian, Chamorro, Niuean, Tokelauan, Tuvaluan, Rotokas

**African Languages (Latin Script):**

- Afrikaans, Swahili, Hausa (Latin), Yoruba, Igbo, Zulu, Xhosa, Shona, Chichewa, Sotho, Tswana, and many other African languages using extended Latin characters

**Constructed Languages:**

- Esperanto, Ido, Interlingua (all use Latin script with diacritics)

### Languages with Partial SBCS Support

Some languages can be represented in SBCS but may require compromises:

- Languages using combining diacritics (some characters may require multiple bytes in practice)
- Languages with extensive character sets that may need multiple code pages

## Additional Notes

### Language-Specific Considerations

**Vietnamese:** Vietnamese requires 134 non-ASCII letters due to letters taking both modifier diacritics and tone marks. Windows-1258 uses combining diacritics to fit within 256 characters. VISCII and VSCII use precomposed characters.

**Pacific Languages:** Many Polynesian languages (Hawaiian, Maori, Tongan, etc.) can be encoded in SBCS using Latin script with macrons and other diacritics. CP1252 or ISO-8859-1 can accommodate most of these languages.

**African Languages:** Many African languages written in Latin script can be encoded in SBCS, though some may require extended Latin characters. Languages like Swahili use only basic Latin characters and are fully compatible with ASCII/ISO-8859-1.

**Constructed Languages:** Esperanto, Ido, and Interlingua all use Latin script with diacritics and can be encoded in SBCS encodings like ISO-8859-1 or CP1252.

## Notes on Implementation

1. **Encoding Compatibility:** Many encodings are similar but not identical. For example, Windows-1252 and ISO-8859-1 differ in the C1 control area (128-159).

2. **Character Limitations:** SBCS encodings are limited to 256 characters, which may not be sufficient for languages with:
   - Large character sets (Chinese, Japanese, Korean require MBCS/DBCS)
   - Extensive use of combining diacritics
   - Complex writing systems

3. **Modern Usage:** While SBCS encodings are still used in legacy systems, modern applications should prefer UTF-8 for maximum compatibility and language support.

4. **Game Compatibility:** For KOTOR, only 8-bit encodings are compatible. Languages requiring more than 256 characters cannot be fully represented.

5. **Encoding Selection:** When multiple encodings are available for a language (e.g., Cyrillic can use CP1251, ISO-8859-5, or KOI8-R), choose based on:
   - Platform compatibility (Windows vs. Unix)
   - Legacy system requirements
   - Character coverage needs
   - Regional preferences

6. **Language Enum Limitations:** The PyKotor `Language` enum currently supports 128 SBCS languages (IDs 0-127). IDs 128+ are reserved for non-SBCS languages (Korean, Chinese, Japanese). This means that while hundreds of languages can theoretically be represented in SBCS encodings, only the most commonly used or requested languages are included in the enum. Additional languages can be added if:
   - The ID space is expanded (e.g., using a different numbering scheme)
   - Less commonly used languages are removed to make room
   - A hierarchical or grouped approach is adopted

## Comprehensive Language List (SBCS-Compatible)

The following is an exhaustive list of languages that can be represented using SBCS encodings, organized by script and encoding family. Note that not all of these are currently in the `Language` enum due to ID space limitations.

### Latin Script Languages (CP1252 / ISO-8859-1 / ISO-8859-15)

**European Languages:**
- All Western European languages (English, French, German, Spanish, Italian, Portuguese, Dutch, etc.)
- All Nordic languages (Danish, Norwegian, Swedish, Finnish, Icelandic, Faroese)
- All Celtic languages (Irish, Scottish Gaelic, Welsh, Breton, Cornish, Manx)
- Romance languages: Catalan, Galician, Occitan, Aragonese, Asturian, Mirandese, Sardinian, Sicilian, Neapolitan, Venetian, Lombard, Piedmontese, Ligurian, Emilian-Romagnol, Romansh, Ladin, Friulian, Walloon, Corsican
- Germanic languages: Afrikaans, Frisian, Luxembourgish, Low German, Yiddish (Latin variant), Alemannic, Bavarian, Limburgish, Pennsylvania German
- Slavic languages (Latin script): Polish, Czech, Slovak, Croatian, Slovenian, Serbian (Latin), Bosnian, Montenegrin (Latin), Kashubian, Silesian, Rusyn (Latin variant), Sorbian
- Other: Albanian, Basque, Estonian, Latvian, Lithuanian, Latgalian, Maltese, Hungarian, Romanian, Turkish, Azeri (Latin), Uzbek (Latin), Turkmen (Latin), Kazakh (Latin variant), Kyrgyz (Latin variant), Tatar (Latin variant)

**African Languages (Latin Script):**
- West African: Hausa, Yoruba, Igbo, Fulfulde, Bambara, Malinke, Wolof, Twi, Akan, Ga, Dagbani, Soninke, Mandinka, Susu, Temne, Mende, Kpelle, Vai, Ewe, Fon, Grebo
- East African: Swahili, Kinyarwanda, Luganda, Kikuyu, Kirundi, Ndebele, Sango
- Southern African: Zulu, Xhosa, Shona, Chichewa, Sotho, Tswana, Venda, Tsonga, Bemba, Lingala, Kongo

**Austronesian Languages (Latin Script):**
- Philippine: Tagalog, Filipino, Cebuano, Ilocano, Waray, Hiligaynon, Bicol, Kapampangan, Pangasinan
- Indonesian/Malay: Indonesian, Malay, Javanese, Sundanese, Madurese, Minangkabau, Acehnese, Balinese, Buginese, Batak languages
- Pacific: Hawaiian, Maori, Tahitian, Tongan, Samoan, Fijian, Chamorro, Niuean, Tokelauan, Tuvaluan, Rotokas, Nauruan, Marshallese, Gilbertese, Pohnpeian, Kosraean, Palauan, Yapese
- Other: Malagasy

**Other Languages (Latin Script):**
- Constructed: Esperanto, Ido, Interlingua, Volapük
- Creoles: Haitian Creole, Papiamento, Tok Pisin, Bislama
- Indigenous Americas: Guarani, Quechua, Aymara, Nahuatl (Latin variant), and many others using Latin script
- Historical/Classical: Latin

### Cyrillic Script Languages (CP1251 / ISO-8859-5 / KOI8-R / KOI8-U / CP855 / CP866)

**Slavic Languages:**
- Russian, Ukrainian, Belarusian, Bulgarian, Macedonian, Serbian (Cyrillic), Montenegrin (Cyrillic), Rusyn

**Turkic Languages:**
- Kazakh, Kyrgyz, Tatar, Bashkir, Chuvash, Karachay-Balkar, Nogai, Yakut, Tuvan, Khakas, Altai, Uyghur (Cyrillic variant), Azerbaijani (Cyrillic variant, historical)

**Iranian Languages:**
- Tajik, Ossetian

**Mongolic Languages:**
- Mongolian, Buryat, Kalmyk

**Caucasian Languages:**
- Abkhaz, Chechen, Ingush, Avar, Lezgian, Kabardian, Adyghe

**Uralic Languages:**
- Komi, Mari, Udmurt, Erzya, Moksha, Karelian

**Other:**
- Moldovan (Cyrillic variant, historical), Gagauz (Cyrillic variant)

### Arabic Script Languages (CP1256 / ISO-8859-6)

**Semitic Languages:**
- Arabic (all varieties), Maltese (historical Arabic script)

**Iranian Languages:**
- Persian (Farsi), Dari, Tajik (Arabic script variant), Kurdish, Balochi

**Indo-Aryan Languages:**
- Urdu, Sindhi, Kashmiri (Arabic script variant), Punjabi (Shahmukhi)

**Turkic Languages:**
- Uyghur (Arabic script), Kazakh (Arabic script variant, historical), Kyrgyz (Arabic script variant, historical)

**Austronesian Languages:**
- Jawi (Malay), Pegon (Indonesian), Chavacano (Arabic script variant)

**African Languages:**
- Hausa (Ajami), Swahili (Arabic script variant), Fulfulde (Ajami), Wolof (Ajami), Mandinka (Ajami)

**Dravidian Languages:**
- Arwi (Tamil Arabic script)

**Other:**
- Pashto, Brahui

### Greek Script Languages (CP1253 / ISO-8859-7)

- Modern Greek, Ancient Greek (with polytonic orthography - may require extended encoding), Cypriot Greek, Pontic Greek, Cappadocian Greek, Tsakonian

### Hebrew Script Languages (CP1255 / ISO-8859-8)

- Hebrew (Modern and Biblical), Yiddish (Hebrew script - traditional), Ladino (Hebrew script variant - historical), Judeo-Arabic (Hebrew script variant - historical)

### Thai Script Languages (CP874 / ISO-8859-11 / TIS-620)

- Thai, Southern Thai, Northern Thai (Lanna), Isan (Thai script variant), Lao (Thai script variant - historical)

### Vietnamese (CP1258 / VISCII / VSCII)

- Vietnamese (uses combining diacritics in CP1258, precomposed characters in VISCII/VSCII)

### Armenian (ArmSCII-8)

- Armenian (Eastern and Western variants)

### Georgian (GEOSTD8)

- Georgian, Mingrelian, Svan, Laz

### Tamil (TSCII)

- Tamil

## Total Count

Based on this comprehensive analysis, there are approximately **500-700 languages** that can be represented using SBCS encodings, depending on:
- Whether historical variants are counted
- Whether script variants of the same language are counted separately
- Whether dialects with distinct orthographies are counted

The PyKotor `Language` enum currently includes **128 SBCS languages** (IDs 0-127), representing the most commonly used languages that can be encoded in SBCS. This covers the vast majority of use cases for game localization while remaining within practical ID space limitations.

## Complete Language-to-Encoding Mapping

### By Primary Encoding

**CP1252 / ISO-8859-1:**
- Western European languages (English, French, German, Spanish, Italian, Portuguese, Dutch, etc.)
- Nordic languages (Danish, Norwegian, Swedish, Finnish, Icelandic)
- Celtic languages (Irish, Scottish Gaelic, Welsh, Breton, Cornish, Manx)
- Other: Afrikaans, Swahili, Indonesian, Latin, Esperanto, Maltese, Albanian, Basque, Catalan, Galician, Luxembourgish, Faroese, Frisian, Occitan
- Pacific languages: Hawaiian, Maori, Tahitian, Tongan, Samoan, Fijian, Chamorro, Niuean, Tokelauan, Tuvaluan, Rotokas
- African languages: Swahili, Hausa (Latin), Yoruba, Igbo, Zulu, Xhosa, Shona, Chichewa, Sotho, Tswana
- Constructed languages: Esperanto, Ido, Interlingua
- Southeast Asian: Tagalog, Filipino, Indonesian

**CP1250 / ISO-8859-2:**
- Central/Eastern European: Czech, Slovak, Polish, Hungarian, Romanian, Croatian, Serbian (Latin), Slovenian, Bosnian, Montenegrin

**CP1251 / ISO-8859-5 / KOI8-R / KOI8-U:**
- Cyrillic Slavic: Russian, Ukrainian, Belarusian, Bulgarian, Macedonian, Serbian (Cyrillic), Montenegrin (Cyrillic), Rusyn
- Cyrillic Turkic: Kazakh, Kyrgyz, Tatar, Bashkir, Chuvash, Karachay-Balkar, Nogai, Yakut, Tuvan, Khakas, Altai, Uyghur (Cyrillic variant)
- Cyrillic Iranian: Tajik, Ossetian
- Cyrillic Mongolic: Mongolian, Buryat, Kalmyk
- Cyrillic Caucasian: Abkhaz, Chechen, Ingush, Avar, Lezgian, Kabardian, Adyghe
- Cyrillic Uralic: Komi, Mari, Udmurt, Erzya, Moksha, Karelian
- Other Cyrillic: Moldovan (Cyrillic variant, historical), Gagauz (Cyrillic variant)

**CP1253 / ISO-8859-7:**
- Greek

**CP1254 / ISO-8859-9:**
- Turkish, Azeri (Latin), Uzbek (Latin)

**CP1255 / ISO-8859-8:**
- Hebrew

**CP1256 / ISO-8859-6:**
- Arabic, Farsi (Persian), Urdu, Pashto, Kurdish, Sindhi, Balochi, Uyghur (Arabic script variant), Jawi (Malay Arabic script), Pegon (Indonesian Arabic script), Arwi (Tamil Arabic script), Hausa (Ajami - Arabic script variant), Swahili (Arabic script variant)

**CP1257 / ISO-8859-13:**
- Baltic: Estonian, Latvian, Lithuanian, Latgalian, Polish

**CP1258:**
- Vietnamese (with combining diacritics)

**CP874 / ISO-8859-11 / TIS-620:**
- Thai

**ISO-8859-14:**
- Celtic: Welsh, Irish Gaelic, Scottish Gaelic, Manx, Cornish, Breton

**ISO-8859-15:**
- Western European (revision of ISO-8859-1 with Euro sign)

**ISO-8859-16:**
- South-Eastern European: Albanian, Croatian, Hungarian, Italian, Polish, Romanian, Serbian, Slovenian

**ArmSCII-8:**
- Armenian

**GEOSTD8:**
- Georgian

**TSCII:**
- Tamil

## References

- ISO/IEC 8859 series standards (ISO/IEC 8859-1 through 8859-16)
- Microsoft Windows Code Page documentation
- IANA Character Sets registry (https://www.iana.org/assignments/character-sets)
- Unicode Consortium documentation
- RFC 1456 (VISCII)
- RFC 1489 (KOI8-R)
- RFC 2319 (KOI8-U)
- Various vendor documentation (IBM, Apple, etc.)
- TCVN 5712:1993 (Vietnamese Standard Code for Information Interchange)
- TIS-620 (Thai Industrial Standard 620-2533)