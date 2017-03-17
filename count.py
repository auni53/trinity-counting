import json
import csv
import sys
from os import listdir
from os.path import isfile, join
import pdb

stop = pdb.set_trace

def process(filename):
  '''
  filename -> (title, candidates, ballots)
  '''

  with open(filename) as file:
    title = 0
    start = 0
    ballots = []
  
    csv_file = csv.reader(file, delimiter='\t')
    lines = list(csv_file)

    for l in lines:
      if start == 1:
        ballots.append(l)
      if title == 0:
        title = l[0]
        winner_i = l.index('Num1')
      if l != [] and l[0] == 'socialyos':
        start = 1

    candidates = []
    for b in ballots:
      if (not b[winner_i] in candidates):
        candidates.append(b[winner_i])
    return (title, candidates, ballots)
  
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
  print()
  print("~~%s~~" % title)
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

      print("\nROUND %d" % r)
      tally = getBlankTally(validCandidates)
      validBallots = filter(validBallots, validCandidates)
      for b in validBallots:
        try:
          tally[b[0]] += 1
        except KeyError:
          print('--KEY ERROR--')
          print(title)
          print(validCandidates)

      least = min(tally.values())
      for key in tally:
        if tally[key] == least:
          validCandidates.remove(key)

      for key in candidates:
        if key in tally:
          table[key].append(tally[key])
          print(key, tally[key])
        else:
          table[key].append('*')
          print(key, '*')
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

  mypath = 'results/'
  fileList = [f for f in listdir(mypath) if (isfile(join(mypath, f)) and f[0] != '.' and f.split('.')[1] == 'xls')]
  
  for filename in fileList:
    try:
      data = process(mypath + filename)
    except UnicodeDecodeError:
      print("--ERROR--")
      print(filename)

    # temp bc no position name look up
    data = (filename.split('.')[0], data[1], data[2])
    result = count(data[0], data[1], data[2])

    c = 0
    while c < len(result):
      title = data[0]
      if len(result) > 1:
        title += ' Winner #' + str(c + 1)
      results[title] = result[c]
      c += 1
  
  # print(json.dumps(results))
