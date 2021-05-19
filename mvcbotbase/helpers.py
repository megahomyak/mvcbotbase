def enumerate_strings(strings):
    return (
        f"{number}. {string}"
        for number, string in enumerate(strings, start=1)
    )


def enumerate_and_join_strings(strings, separator="\n"):
    return separator.join(enumerate_strings(strings))
