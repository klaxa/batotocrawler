batotocrawler
=============

Crawls Batoto or KissManga for manga.

# REQUIREMENTS
- Python 3.2.3 (untested on older versions)
- [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/)

# USAGE
    Manager.py [options] URL ...

# OPTIONS
    -s NUMBER                       chapter to start downloading from.
    -e NUMBER                       chapter to end the downloading at.
    -d DIRECTORY                    directory (absolute or relative) to download to. use '%title'
                                    to use the manga title as directory name or '%title_' to use
                                    use the manga title with spaces replaced by underscores as
                                    directory name.
    -q, --quiet                     quiet mode: supresses info output (but not interactive
                                    output).
    --debug                         debug mode: print various debugging information.
    --cbz                           files are zipped with a ".cbz" extension instead of ".zip".
    --server SERVER                 choose the download server to use. currently only works with
                                    Batoto (img1 through img4).
    --interactive                   asks which chapter to keep in case of duplicate releases for
                                    a single chapter.
    --prefer-group GROUP_NAME       will keep the chapter by GROUP_NAME in case of duplicate
                                    releases for a single chapter.

These options can also be added in a configuration file in `~/.config/batotocrawler.conf` to be always executed.
