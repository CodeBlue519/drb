#!/bin/sh
# drb: Read the Douay-Rheims Bible from your terminal
# License: Public domain

SELF="$0"

get_data() {
	sed '1,/^#EOF$/d' < "$SELF" | tar xzf - -O "$1"
}

if [ -z "$PAGER" ]; then
	if command -v less >/dev/null; then
		PAGER="less"
	else
		PAGER="cat"
	fi
fi

show_help() {
	exec >&2
	echo "usage: $(basename "$0") [flags] [reference...]"
	echo
	echo "  -l      list books"
	echo "  -r      random verse"
	echo "  -c      show commentary (Haydock)"
	echo "  -W      no line wrap"
	echo "  -h      show help"
	echo
	echo "  Reference types:"
	echo "      <Book>"
	echo "          Individual book"
	echo "      <Book>:<Chapter>"
	echo "          Individual chapter of a book"
	echo "      <Book>:<Chapter>:<Verse>[,<Verse>]..."
	echo "          Individual verse(s) of a specific chapter of a book"
	echo "      <Book>:<Chapter>-<Chapter>"
	echo "          Range of chapters in a book"
	echo "      <Book>:<Chapter>:<Verse>-<Verse>"
	echo "          Range of verses in a book chapter"
	echo "      <Book>:<Chapter>:<Verse>-<Chapter>:<Verse>"
	echo "          Range of chapters and verses in a book"
	echo
	echo "      /<Search>"
	echo "          All verses that match a pattern"
	echo "      <Book>/<Search>"
	echo "          All verses in a book that match a pattern"
	echo "      <Book>:<Chapter>/<Search>"
	echo "          All verses in a chapter of a book that match a pattern"
	exit 2
}

while [ $# -gt 0 ]; do
	isFlag=0
	firstChar="${1%"${1#?}"}"
	if [ "$firstChar" = "-" ]; then
		isFlag=1
	fi

	if [ "$1" = "--" ]; then
		shift
		break
	elif [ "$1" = "-l" ]; then
		get_data drb.tsv | awk -v cmd=list "$(get_data drb.awk)"
		exit
	elif [ "$1" = "-r" ]; then
		total=$(get_data drb.tsv | wc -l)
		line=$(awk 'BEGIN{srand(); print int(rand()*'"$total"')+1}')
		get_data drb.tsv | awk -v cmd=random -v line="$line" "$(get_data drb.awk)"
		exit
	elif [ "$1" = "-c" ]; then
		export DRB_COMMENTARY=1
		shift
	elif [ "$1" = "-W" ]; then
		export DRB_NOLINEWRAP=1
		shift
	elif [ "$1" = "-h" ] || [ "$isFlag" -eq 1 ]; then
		show_help
	else
		break
	fi
done

if cols=$(tput cols 2>/dev/null); then
	export DRB_MAX_WIDTH="$cols"
fi

if [ $# -eq 0 ]; then
	if [ ! -t 0 ]; then
		show_help
	fi

	while true; do
		printf "drb> "
		if ! read -r ref; then
			break
		fi
		get_data drb.tsv | awk -v cmd=ref -v ref="$ref" "$(get_data drb.awk)" | ${PAGER}
	done
	exit 0
fi

(
get_data drb.tsv | awk -v cmd=ref -v ref="$*" "$(get_data drb.awk)"
if [ "${DRB_COMMENTARY:-0}" = "1" ]; then
	# Extract book and chapter:verse from the reference for commentary lookup
	get_data drb.tsv | awk -v cmd=ref -v ref="$*" '
	'"$(get_data drb.awk)"'
	' | while IFS= read -r line; do true; done
	# Simpler: grep commentary by matching verses that were displayed
	echo ""
	echo "--- Haydock Commentary ---"
	echo ""
	get_data drb.tsv | awk -v cmd=ref -v ref="$*" "$(get_data drb.awk)" | \
	sed -n 's/^\([A-Za-z0-9 ]*\)$/BOOK:\1/p; s/^\([0-9]*:[0-9]*\)\t.*/\1/p' | \
	while IFS= read -r line; do
		case "$line" in
			BOOK:*) curbook="${line#BOOK:}" ;;
			*) get_data haydock.tsv | grep "^${curbook}	${line}	" | cut -f3 | \
			   awk -v verse="$line" 'BEGIN{printf "  %s\t", verse}{print}' ;;
		esac
	done
fi
) | ${PAGER}
