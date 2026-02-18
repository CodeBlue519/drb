_drb_comp() {
    COMPREPLY=( $(compgen -W "$1" -- ${word}) )
    if [[ ${#COMPREPLY[@]} == 1 && ${COMPREPLY[0]} == "--"*"=" ]]; then
        complete -o nospace
    fi
}

_drb() {
    COMPREPLY=()
    complete +o default

    local word="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"

    case "${COMP_CWORD}" in
        1)
            if [[ $word == -* ]]; then
                _drb_comp '-l -W -h'
            else
                drb -l | while read b;
                    do echo ${b% *}
                done
            fi
            ;;
    esac
}
complete -F _drb drb
