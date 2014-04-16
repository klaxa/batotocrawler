batotocrawler
=============

Cralws batoto for mangas.

# USAGE
    Manager.py [options] URL

# OPTIONS
    -s NUMBER                        chapter to start downloading from
    -e NUMBER                        chapter to end the downloading at
    -q, --quiet                      quiet mode: supresses info output
                                     (but not interactive output)
    --interactive                    asks which chapter to keep in case of
                                     duplicate releases for a single chapter
    --prefer-group GROUP_NAME        will keep the chapter by GROUP_NAME in
                                     case of duplicate releases for a single
                                     chapter

These options can also be added in a configuration file in `~/.config/batotocrawler.conf` to be always executed.