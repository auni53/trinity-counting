import json
import csv
import sys
from os import listdir
from os.path import isfile, join

def process(filename):
  '''
  filename -> (title, candidates, ballots)
  '''

  try:
    with open(filename) as file:
      title = 0
      start = 0
      ballots = []

      csv_file = csv.reader(file, delimiter='\t')
      lines = list(csv_file)
      for l in lines:
        newL = []
        if start == 1:
          ballots.append(l[2:])
        if title == 0:
          title = l[0]
        if l != [] and l[0] == 'socialyos':
          start = 1
        if (len(ballots) == 40 and False):
          break
      candidates = []
      for b in ballots:
        if (not b[0] in candidates):
          candidates.append(b[0])
      return (title, candidates, ballots)
  except FileNotFoundError:
    return False

def getBlankTally(candidates):
  tally = {}
  for name in candidates:
    tally[name] = 0
  return tally

def filter(ballots, candidates):
  newBallots = []
  for b in ballots:
    newB = []
    for name in b:
      if (name in candidates):
        newB.append(name)
    if len(newB) != 0:
      newBallots.append(newB)
  return newBallots

def isDone(tally):
  total = 0
  for key in tally:
    total += tally[key]

  for key in tally:
    if tally[key] > (total / 2):
      return key
  return False

def count(title, candidates, ballots, n=1):
  # print()
  # print("~~%s~~" % title)
  winners = []
  tables = []
  while n > 0:

    table = {}
    for key in candidates:
      table[key] = []

    validCandidates = candidates[:]
    validBallots = ballots[:]
    tally = getBlankTally(validCandidates)
    for w in winners:
      validCandidates.remove(w)
    r = 1

    while not isDone(tally): # len(validCandidates) > 1:
      tally = getBlankTally(validCandidates)
      validBallots = filter(validBallots, validCandidates)
      for b in validBallots:
        try:
          tally[b[0]] += 1
        except KeyError:
          print('--KEY ERROR--')
          print(title)
          print(validCandidates)
    #   print()

      try:
          least = min(tally.values())
          for key in tally:
            if tally[key] == least:
              validCandidates.remove(key)
      except ValueError:
          print('--VALUE ERROR--')
          print(title)
          print(validCandidates)
          return

      for key in candidates:
        if key in tally:
          table[key].append(tally[key])
        #   print(key, tally[key])
        else:
          table[key].append('*')
        #   print(key, '*')
      r += 1
    tables.append(table)
    winners.append(isDone(tally))
    n -= 1

  return tables

def getN(title):

  keywords = ['Athletics', 'TCDS', 'TCES']
  for k in keywords:
    if k in title:
      return 2

  if 'Senate' in title:
    return 3

  return 1

if __name__ == '__main__':

  results = {}

  if len(sys.argv) >= 2:
    filename = str(sys.argv[1])
    if len(sys.argv) == 3:
      positions = int(sys.argv[2])
    else:
      positions = 1
    data = process(filename)
    if data:
      print(data[0], data[1], positions)
      count(data[0], data[1], data[2], positions)
    else:
      print("File not found.")
  else:
    mypath = 'week2'
    fileList = [f for f in listdir(mypath) if (isfile(join(mypath, f)) and f[0] != '.' and f.split('.')[1] == 'xls')]

    # fileList = ['../excelfile (21).xls']
    for filename in fileList:
      try:
          data = process('week2/' + filename)
      except UnicodeDecodeError:
          print("--ERROR--")
          print(filename)

    #   print(data[0], filename)
      if (getN(data[0]) == 3 or True):
          result = count(data[0], data[1], data[2], getN(data[0]))

          c = 0
          while c < len(result):
            title = data[0]
            if len(result) > 1:
              title += ' Winner #' + str(c + 1)
            results[title] = result[c]
            c += 1

    print(json.dumps(results))
