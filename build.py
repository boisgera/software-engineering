#!/usr/bin/env python

# Python 3 Standard Library
import pathlib

# Third-Party Libraries
import euldoc
import pandoc
import plumbum

md_file = "index.md"

options = [
    # Standalone
    "--standalone",
    # Table of contents
    "--toc",
    "--toc-depth=3",
    # Typography
    # "--smart",
    # Language
    "-V",
    "lang=en",
    # Misc.
    "--section-divs",
    "--mathjax",
    "--email-obfuscation=none",
]

doc = pandoc.read(file=md_file)
doc = euldoc.html_transform(doc)
html_file = str(pathlib.Path(md_file).with_suffix(".html"))
pandoc.write(doc, file=html_file, format="html5", options=options)

eul_style = plumbum.local["eul-style"]
html_post = eul_style(html_file)
with open(html_file, "w") as file:
    file.write(html_post)


"""
set -o errexit
set -o pipefail
shopt -sq nullglob

# Options Handling
# ==============================================================================
fast=false
verbose=false

for arg in "$@"; do
  case $arg in
    -f|--fast)
      fast=true
      ;;
    -v|--verbose)
      verbose=true
      ;;
    -q|--quiet)
      verbose=false
      ;;
  esac
done

if $verbose; then
  echo
  echo fast=$fast
  echo verbose=$verbose
  set -v
fi

# Document
# ==============================================================================

# TODO: try the .md extension?
# TODO: loop over all text files ?
# TODO: use some config info?

# wrt config: the scheme could be: search for a (YAML, JSON, TOML) config file, 
# if not found, generate it with some defaults, otherwise load the user config?
# Don't change the current user process, only allow another one for power
# users.

txt_file() {
  txt_files=(*.txt)
  local len=${#txt_files[@]}
  if [ $len = 0 ]; then
    echo "error: no txt file found"
    exit 1
  elif [ $len -gt 1 ]; then
    echo "error: several txt files found"
    exit 1
  else
    echo "${txt_files[0]}"
  fi
}

txt=$(txt_file)
doc="${txt%.*}"

# Bibliography
# ==============================================================================
bib_yaml=(bibliography/*.yaml)
for filename in "${bib_yaml[@]}"; do
  pandoc-citeproc -j "${filename}" > "${filename}".json
done
bib_json=(bibliography/*.json)

# Images
# ==============================================================================
images=
if [ -d images ]; then
  images="images"
fi

# Variables
# ==============================================================================
TOC=("--toc" "--toc-depth=3")
TYPO=("--smart")
LANG_=("-V" "lang=en") # don't shadow the LANG variable.
BIBFILES_OPT=()
BIB_OPT=()
if [ "${#bib_json[@]}" -gt 0 ]; then
  for filename in "${bib_json[@]}"; do
    BIBFILES_OPT+=("--bibliography=${filename}")
  done
  BIB_OPT=("-M" "link-citations=true" "${BIBFILES_OPT[@]}")
fi

SHARED_OPT=("${LANG_[@]}" "${TOC[@]}" "${TYPO[@]}")
JSON_OPT=("-t" "json" "${SHARED_OPT[@]}" "${BIB_OPT[@]}")
PDF_OPT=("${SHARED_OPT[@]}" "--latex-engine=xelatex")
HTML_OPT=("-t" "html5" "${SHARED_OPT[@]}" 
          "--section-divs" "--mathjax" "--email-obfuscation=none")

txt="${doc}.txt"
pdf="${doc}.pdf"
html="${doc}.html"
json="${doc}.json"
zip="${doc}.zip"
# Temp files
json_html="${doc}.html.json"
json_pdf="${doc}.pdf.json"

# Main
# ==============================================================================

# Install Templates
# ------------------------------------------------------------------------------
mkdir -p templates && cp -r /usr/share/pandoc-templates/. templates
PDF_OPT+=("--template=templates/template.latex")
HTML_OPT+=("--template=templates/template.html5")

# Generate images
# ------------------------------------------------------------------------------
if ! $fast && [ $images ] && [ -e images/main.py ]; then
    cd $images && python main.py && cd ..
fi

# Generate JSON
# ------------------------------------------------------------------------------
pandoc -o "$json" "${JSON_OPT[@]}" "$txt"

# Generate PDF
# ------------------------------------------------------------------------------
cat "$json" | eul-doc --pdf > "$json_pdf"
pandoc -f json -o "$pdf" "${PDF_OPT[@]}" "$json_pdf"
rm "$json_pdf"

# Generate HTML
# ------------------------------------------------------------------------------
cat "$json" | eul-doc --html > "$json_html"
pandoc -f json "${HTML_OPT[@]}" "$json_html" > "_$html"
rm "$json_html"

eul-style "${BIBFILES_OPT[@]}" "_$html" > "$html" && rm "_$html"

# Generate ZIP File
# ------------------------------------------------------------------------------
target="build_zip/${doc}" 
mkdir -p "${target}"
cp -rf "$txt" "$html" "$pdf" "${target}"
if [ "$BIB_OPT" ]; then
  cp -rf bibliography "${target}/bibliography"
fi
if [ "$images" ]; then
  cp -rf "$images" "${target}"
fi
cd build_zip && zip -r "${zip}" "${doc}" >> /dev/null && cp "${zip}" .. 
cd .. && rm -rf build_zip

"""
