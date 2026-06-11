#!/usr/bin/env bash
# Language Fallback Resolver — Show fallback chains for Wikimedia languages
# Usage:
#   ./language-fallback.sh fr              — Show fallback chain for French
#   ./language-fallback.sh be-tarask      — Show fallback for special code
#   ./language-fallback.sh --list          — Show all fallback chains
#   ./language-fallback.sh --help

set -eo pipefail

UA="language-fallback/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; user@example.com) WMSkills"

usage() {
    grep '^#' "$0" | sed 's/^# \?//' | sed '$d'
    exit 0
}

if [ $# -eq 0 ]; then
    usage
fi

# Lookup function: looks up the fallback chain for a language code
# Data is stored as "code:chain" pairs in the script data section below
lookup_fallback() {
    local lang="$1"
    grep "^$lang:" "$0" | tail -1 | cut -d: -f2-
}

case "$1" in
    --help|-h) usage ;;
    --list|-l)
        echo "Language Fallback Chains"
        echo "========================"
        grep -v '^#' "$0" | grep '^[a-z]' | sort | while IFS=: read -r lang chain; do
            if [ -n "$lang" ] && [ -n "$chain" ]; then
                echo "  $lang → $chain"
            fi
        done
        exit 0
        ;;
    *)
        LANG="$1"
        CHAIN=$(lookup_fallback "$LANG")
        if [ -z "$CHAIN" ]; then
            if [ "$LANG" = "en" ]; then
                echo "en: (no fallback — English is the ultimate fallback)"
            else
                echo "Warning: No fallback chain known for '$LANG'. Defaulting to 'en'."
                echo "$LANG → en"
            fi
        else
            echo "$LANG → $CHAIN"
        fi
        exit 0
        ;;
esac

# Language fallback data — format: language_code:fallback1,fallback2,...
# This section acts as a lookup table (no associative arrays needed)
# Data sourced from MediaWiki i18n fallback chains
# Romance
fr:en
es:en
it:en
pt:es,en
pt-br:pt,en
ro:en
ca:en
gl:pt,es,en
oc:fr,en
ast:es,en
ext:es,en
mwl:pt,es,en
pms:it,fr,en
fur:it,en
lmo:it,en
nap:it,en
scn:it,en
vec:it,en
co:fr,it,en
# Germanic
de:en
nl:en
sv:en
da:en
no:nb
nb:nn,en
nn:nb,no,en
is:en
fo:da,en
fy:nl,en
nds:de,en
nds-nl:nds,nl,en
li:nl,en
zea:nl,en
# Slavic
ru:en
pl:en
uk:ru,en
cs:en
sk:cs,en
bg:en
sr:en
sh:sr,hr,bs,en
hr:en
bs:hr,en
sl:en
mk:en
be:ru,en
be-tarask:be,ru,en
rue:uk,ru,en
szl:pl,en
dsb:de,en
hsb:dsb,de,en
cu:ru,en
# Uralic
fi:en
et:en
hu:en
se:nb,fi,en
smn:fi,en
sms:fi,en
# Baltic
lt:en
lv:en
sgs:lt,en
# Hellenic
el:en
# Celtic
ga:en
gd:en
cy:en
br:fr,en
kw:en
gv:en
# Semitic
ar:en
he:en
fa:en
ps:en
ur:en
ckb:ar,en
am:en
# Turkic
tr:en
az:en
azb:az,tr,en
uz:en
kk:ru,en
ky:ru,en
crh:tr,en
tk:en
tt:ru,en
ba:ru,en
sah:ru,en
# East Asian
ja:en
ko:en
zh:en
yue:zh-hant,zh,en
zh-hans:zh,en
zh-hant:zh,en
zh-cn:zh-hans,zh,en
zh-tw:zh-hant,zh,en
zh-hk:zh-hant,zh,en
# Southeast Asian
th:en
vi:en
lo:th,en
km:en
my:en
mn:ru,en
bo:zh,en
# South Asian
hi:en
bn:en
ta:en
te:en
kn:en
ml:en
mr:en
gu:en
pa:en
or:en
as:bn,en
ne:hi,en
si:en
sd:en
ks:ur,en
pi:hi,en
sa:hi,en
dty:ne,hi,en
mai:hi,en
gom:hi,en
# African
af:nl,en
sw:en
xh:af,en
zu:af,en
st:af,en
tn:af,en
nso:af,en
ss:af,en
rw:en
rn:en
sn:en
mg:fr,en
mt:en
eu:es,en
ht:fr,en
jv:id,en
su:id,en
min:id,en
ace:id,en
bug:id,en
bjn:id,en
sg:fr,en
ln:fr,en
lg:en
