import csv
# Exports the data dictionary to the specified
# csv file
def exportToCSV(dict, csvFileName):
    print("Generating \'"+csvFileName+"\'...")
    try:
        with open(csvFileName, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(dict.keys())
            writer.writerows(zip(*dict.values()))
    except:
        print("Error: unable to write to \'"+csvFileName+"\'. Make sure you have "+
            "permission to write to this file and it is not currently open and try again")