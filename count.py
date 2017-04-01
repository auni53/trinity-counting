import json
import csv
import sys
from os import listdir
from os.path import isfile, join, basename

from pprint import pprint
from argparse import ArgumentParser
import yaml
import pdb

stop = pdb.set_trace
V = 1

def main():
  p = ArgumentParser()
  p.add_argument('-c', nargs='?')
  p.add_argument('-f', nargs='?')
  p.add_argument('-d', nargs='?')
  p.add_argument('-o', nargs='?')
  p.add_argument('-n', action='store_const', const=1, default=0)
  p.add_argument('-w')

  config_filename = p.parse_args().c
  result_filename = p.parse_args().f
  results_directory = p.parse_args().d
  output_path = p.parse_args().o
  dry = p.parse_args().n
  export_web = p.parse_args().w

  results = {}
  def _run(result_filename, config_filename, dry):
    (title, candidates, ballots) = process(result_filename, config_filename)

    breakdown = count(title, candidates, ballots, n=_getN(title), stdout=dry)
    if len(breakdown) == 1: return { title: breakdown[0] }
    else:
      result = {}
      c = 1
      for counting_round in breakdown:
        result['%s Winner #%d' % ( title, c)] = counting_round
        c += 1
      return result

  if result_filename:
    result = _run(result_filename, config_filename, dry)
    results.update(result)
    
  elif results_directory:
    path = p.parse_args().d
    fileList = [f for f in listdir(path) if (isfile(join(path, f)) and f[0] != '.' and f.split('.')[1] == 'xls')]
    
    for filename in fileList:
      result_filename = "%s/%s" % ( path, filename )
      result = _run(result_filename, config_filename, dry)
      results.update(result)

  else:
    raise Exception('No input given.') 
      
  if output_path:
    if output_path == 'print':
      pprint(results)
    with open(output_path, 'w') as f:
      yaml.dump({ 'results': results }, f, default_flow_style=False)

  if export_web:
    with open('./template.html') as t:
      template = t.read()

    with open(export_web, 'w') as f:
      f.write(template % json.dumps(results))

def _compare_candidate_lists(config_candidates, result_candidates):
  s = 0
  for candidate in config_candidates:
    if candidate in result_candidates:
      s += 1
  return s

# results_candidates -> { name, candidates }
def compare_to_config(config_filename, result_candidates):
  if config_filename:
    with open(config_filename) as f:
      most_similar_pid = None
      max_similarity = 0
      config = yaml.safe_load(f)
      for pid in config:
        if 'candidates' in config[pid]:
          config_candidates = config[pid]['candidates']
          score = _compare_candidate_lists(config_candidates, result_candidates)
          if score > max_similarity:
            max_similarity = score
            most_similar_pid = pid

      if most_similar_pid:
        return config[most_similar_pid]

  # No match found
  return { 'name': 'N/A', 'candidates': result_candidates }

def clean(s):
  return s.replace('</div>', '').replace('<div>', '').strip()

# filename -> (title, candidates, ballots)
def process(results_filename, config_filename):
  with open(results_filename) as file:
    title = 0
    start = 0
    ballots = []
  
    csv_file = csv.reader(file, delimiter='\t')
    lines = list(csv_file)
    nums = {}

    for l in lines:
      if len(nums) == 0:
        header = l[:]
        title = l[0]
        for item in header:
          if 'Num' in item:
            nums[int(item[-1])] = header.index(item)
      else:
        ballot = []
        for i in range(1, len(l)):
          if i in nums:
            name = clean(l[nums[i]])
            ballot.append(name)
        ballots.append(ballot)

    candidates = []
    for b in ballots:
      name = clean(b[0])
      if (name not in candidates and name != 'Reopen Nominations'):
        candidates.append(name)

    if config_filename:
      try:
        config = read_config(results_filename, config_filename)
        title = config['name']
        candidates = config['candidates']
      except Exception as e:
        print 'ERROR: Missing config for %s' % ( results_filename )

    # if stdout: print '\n' + results_filename
    return (title, candidates, ballots)

def read_config(results, config):
  with open(results) as r:
    filename = basename(r.name).split('.')[0]
    pid = int(filename)

  with open(config) as c:
    config = yaml.safe_load(c)
    return config[pid]

def count(title, candidates, ballots, n=1, stdout=False):
  if stdout: print("~~%s~~" % title)
  winners = []
  tables = []
  candidates.append('Reopen Nominations')
  while n > 0:

    table = {}
    for key in candidates:
      table[key] = []

    validCandidates = candidates[:]
    validBallots = ballots[:]
    tally = _getBlankTally(validCandidates)
    for w in winners:
      try:
        validCandidates.remove(w)
      except Exception as e:
        continue

    round_num = 1
    while not _isDone(tally): # len(validCandidates) > 1:
      if stdout: print("\nROUND %d" % round_num)
      tally = _getBlankTally(validCandidates)
      validBallots = _filter(validBallots, validCandidates)
      for b in validBallots:
        try:
          tally[b[0]] += 1
        except KeyError:
          if stdout: print('--KEY ERROR--')
          if stdout: print(title)
          if stdout: print(validCandidates)

      for key in candidates:
        if key in tally:
          table[key].append(tally[key])
          if stdout: print(key, tally[key])
        else:
          table[key].append('*')
          if stdout: print(key, '*')

      least = min(tally.values())
      for key in tally:
        removed = []
        if tally[key] == least:
          removed.append(key)
          validCandidates.remove(key)
      round_num += 1
       
      if len(validCandidates) == 0:
        break

    winners.append(_isDone(tally))
    tables.append(table)
    n -= 1

  return tables
  
def _getBlankTally(candidates):
  tally = {}
  for name in candidates:
    tally[name] = 0
  return tally

def _filter(ballots, candidates):
  newBallots = []
  for b in ballots:
    newB = []
    for name in b:
      if (name in candidates):
        newB.append(name)
    if len(newB) != 0:
      newBallots.append(newB)
  return newBallots

def _isDone(tally):
  total = 0
  for key in tally:
    total += tally[key]

  for key in tally:
    if tally[key] > (total / 2):
      return key
  return False

def _getN(title):
  if '(2' in title:
    return 2

  if 'Senate' in title:
    return 3

  return 1

if __name__ == '__main__':
  main()
