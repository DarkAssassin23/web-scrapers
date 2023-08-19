# Web Scrapers

About
---------
A collection of web scrapers, written in python, to scrape data from the
following sites:
 - [cpubenchmark.net](https://cpubenchmark.net)
   - Scrapes data from every CPU on the site
 - [videocardbenchmark.net](https://videocardbenchmark.net)
   - Scrapes data from every GPU on the site

Setup
---------
> **Optional**: 
> If you want to run this in a virtual python environment
> to prevent having more python packages than you need installed on 
> your system, you can set up a virtual python environment with the 
> following commands: 
```
python -m venv env
```
Then, for Windows users:
```
env/source/activate.bat
```
For macOS and Linux users:
```
source env/bin/activate
```
**Required:** Install the required python packages with the 
following command:
```
pip install -r requirements.txt
```

If you modified the script and added additional libraries, and 
used a virtual environment, you can easily update the 
requirements.txt file with the following command:
```
pip freeze > requirements.txt
```
Once you're done in the python enviornment, you can exit it with the following command:
```
deactivate
```
------
Usage
------
You can run any of the script use the following command structure:
```bash
./cpubenchmark.py
```
or 
```bash
python cpubenchmark.py
```

Additionally, you can specify your own output file by tacking on a 
`-o` flag. This will tell the script to use that output file rather than the
default  `cpuData.csv` 
as seen here:
```bash
./cpubenchmark.py -o AllCPUsData.csv
```

Lastly, you can also tack on the -p command to add multiprocessing.
By default, it will use all available CPU's
```bash
./cpubenchmark.py -p
```
```bash
./gpubenchmark.py -o GPU_Data/GPUsData.csv -p 6
```
