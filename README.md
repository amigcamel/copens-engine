COPENS Engine

---

## Build

    docker build -t copens_engine .

## Deploy

    docker run -it --rm -p 7878:7878 \
        -v /usr/local/share/cwb/registry:/usr/local/share/cwb/registry \
        -v /var/local/LOPEN/corpus/CWB/data:/var/local/LOPEN/corpus/CWB/data \
        copens_engine

## Commandline usage

    python cli.py -c ptt -t test -w 10 -r 10 -p 1

