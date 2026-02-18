BEGIN {
	FS = "\t"

	MAX_WIDTH = 80
	if (ENVIRON["DRB_MAX_WIDTH"] ~ /^[0-9]+$/) {
		if (int(ENVIRON["DRB_MAX_WIDTH"]) < MAX_WIDTH) {
			MAX_WIDTH = int(ENVIRON["DRB_MAX_WIDTH"])
		}
	}

	if (cmd == "ref") {
		mode = parseref(ref, p)
		p["book"] = cleanbook(p["book"])
	}
}

cmd == "list" {
	if (!($2 in seen_books)) {
		printf("%s (%s)\n", $1, $2)
		seen_books[$2] = 1
	}
}

function parseref(ref, arr) {
	if (match(ref, "^[1-9]?[a-zA-Z ]+")) {
		arr["book"] = substr(ref, 1, RLENGTH)
		ref = substr(ref, RLENGTH + 1)
	} else if (match(ref, "^/")) {
		arr["search"] = substr(ref, 2)
		return "search"
	} else {
		return "unknown"
	}

	if (match(ref, "^:?[1-9]+[0-9]*")) {
		if (sub("^:", "", ref)) {
			arr["chapter"] = int(substr(ref, 1, RLENGTH - 1))
			ref = substr(ref, RLENGTH)
		} else {
			arr["chapter"] = int(substr(ref, 1, RLENGTH))
			ref = substr(ref, RLENGTH + 1)
		}
	} else if (match(ref, "^/")) {
		arr["search"] = substr(ref, 2)
		return "search"
	} else if (ref == "") {
		return "exact"
	} else {
		return "unknown"
	}

	if (match(ref, "^:[1-9]+[0-9]*")) {
		arr["verse"] = int(substr(ref, 2, RLENGTH - 1))
		ref = substr(ref, RLENGTH + 1)
	} else if (match(ref, "^-[1-9]+[0-9]*$")) {
		arr["chapter_end"] = int(substr(ref, 2))
		return "range"
	} else if (match(ref, "^/")) {
		arr["search"] = substr(ref, 2)
		return "search"
	} else if (ref == "") {
		return "exact"
	} else {
		return "unknown"
	}

	if (match(ref, "^-[1-9]+[0-9]*$")) {
		arr["verse_end"] = int(substr(ref, 2))
		return "range"
	} else if (match(ref, "-[1-9]+[0-9]*")) {
		arr["chapter_end"] = int(substr(ref, 2, RLENGTH - 1))
		ref = substr(ref, RLENGTH + 1)
	} else if (ref == "") {
		return "exact"
	} else if (match(ref, "^,[1-9]+[0-9]*")) {
		arr["verse", arr["verse"]] = 1
		delete arr["verse"]
		do {
			arr["verse", substr(ref, 2, RLENGTH - 1)] = 1
			ref = substr(ref, RLENGTH + 1)
		} while (match(ref, "^,[1-9]+[0-9]*"))

		if (ref != "") {
			return "unknown"
		}

		return "exact_set"
	} else {
		return "unknown"
	}

	if (match(ref, "^:[1-9]+[0-9]*$")) {
		arr["verse_end"] = int(substr(ref, 2))
		return "range_ext"
	} else {
		return "unknown"
	}
}

function cleanbook(book) {
	book = tolower(book)
	gsub(" +", "", book)
	return book
}

function bookmatches(book, bookabbr, query) {
	book = cleanbook(book)
	if (book == query) {
		return book
	}

	bookabbr = cleanbook(bookabbr)
	if (bookabbr == query) {
		return book
	}

	if (substr(book, 1, length(query)) == query) {
		return book
	}
}

function printverse(verse,    word_count, characters_printed) {
	if (ENVIRON["DRB_NOLINEWRAP"] != "" && ENVIRON["DRB_NOLINEWRAP"] != "0") {
		printf("%s\n", verse)
		return
	}

	word_count = split(verse, words, " ")
	for (i = 1; i <= word_count; i++) {
		if (characters_printed + length(words[i]) + (characters_printed > 0 ? 1 : 0) > MAX_WIDTH - 8) {
			printf("\n\t")
			characters_printed = 0
		}
		if (characters_printed > 0) {
			printf(" ")
			characters_printed++
		}
		printf("%s", words[i])
		characters_printed += length(words[i])
	}
	printf("\n")
}

function processline() {
	if (last_book_printed != $2) {
		print $1
		last_book_printed = $2
	}

	printf("%d:%d\t", $4, $5)
	printverse($6)
	outputted_records++
}

cmd == "ref" && mode == "exact" && bookmatches($1, $2, p["book"]) && (p["chapter"] == "" || $4 == p["chapter"]) && (p["verse"] == "" || $5 == p["verse"]) {
	processline()
}

cmd == "ref" && mode == "exact_set" && bookmatches($1, $2, p["book"]) && (p["chapter"] == "" || $4 == p["chapter"]) && p["verse", $5] {
	processline()
}

cmd == "ref" && mode == "range" && bookmatches($1, $2, p["book"]) && ((p["chapter_end"] == "" && $4 == p["chapter"]) || ($4 >= p["chapter"] && $4 <= p["chapter_end"])) && (p["verse"] == "" || $5 >= p["verse"]) && (p["verse_end"] == "" || $5 <= p["verse_end"]) {
	processline()
}

cmd == "ref" && mode == "range_ext" && bookmatches($1, $2, p["book"]) && (($4 == p["chapter"] && $5 >= p["verse"] && p["chapter"] != p["chapter_end"]) || ($4 > p["chapter"] && $4 < p["chapter_end"]) || ($4 == p["chapter_end"] && $5 <= p["verse_end"] && p["chapter"] != p["chapter_end"]) || (p["chapter"] == p["chapter_end"] && $4 == p["chapter"] && $5 >= p["verse"] && $5 <= p["verse_end"])) {
	processline()
}

cmd == "ref" && mode == "search" && (p["book"] == "" || bookmatches($1, $2, p["book"])) && (p["chapter"] == "" || $4 == p["chapter"]) && match(tolower($6), tolower(p["search"])) {
	processline()
}

END {
	if (cmd == "ref" && outputted_records == 0) {
		print "Unknown reference: " ref
	}
}
