# -*- coding: utf-8 -*-
# Copyright (c) 2021 Yang, Yun-Tse (Acer.Yang). All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import argparse
import glob
import os.path

region_code_ = {
  '63000': '台北',
  '64000': '高雄',
  '65000': '新北',
  '66000': '台中',
  '67000': '台南',
  '68000': '桃園',
  '10001': '台北',
  '10002': '宜蘭',
  '10003': '桃園',
  '10004': '新竹縣',
  '10005': '苗栗',
  '10007': '彰化',
  '10008': '南投',
  '10009': '雲林',
  '10010': '嘉義縣',
  '10013': '屏東',
  '10014': '台東',
  '10015': '花蓮',
  '10016': '澎湖',
  '10017': '基隆',
  '10018': '新竹市',
  '10019': '台中',
  '10020': '嘉義市',
  '10021': '台南',
  '09007': '連江',
  '09020': '金門',
}

# per 主計處營業項目分類 "中類"
# see https://www.dgbas.gov.tw/public/Attachment/9916134443W75YTOW0.pdf
constructer_codes_ = (41, 42, 43, 71)

constructer_funders_ = set()
constructer_fundings_ = dict()

account_categories_ = (
  '人民團體捐贈收入',
  '個人捐贈收入',
  '其他收入',
  '匿名捐贈',
  '政黨捐贈收入',
  '營利事業捐贈收入',
  '營造業捐贈收入'
)

def getArgs():
  parser = argparse.ArgumentParser()
  parser.add_argument('dir', nargs='?', help='Directory contains election reports')
  parser.add_argument('--tax-id', '-t', action='store_true', help='Print tax ID list')
  parser.add_argument('--funder-csv', '-m', help='CVS contains founder data. e.g. data/funder_with_code.csv. Augment `account` fields if used with |dir|')
  parser.add_argument('--list-constructors', '-l', action='store_true', help='List funders categorized as constructers then exit. Require --funder-csv argument')
  parser.add_argument('--pivot-accounts', '-p', help='Pivot accounts as column headers from input csv')
  parser.add_argument('--preprocess-election-report', '-e')
  return parser.parse_args()

def populate_constructer_info(funder_csv, print_to_stdout):
  with open(args.funder_csv) as f:
    f.readline() # skip header
    for line in f:
      id, name, codes = line.split(',', 2)
      codes = codes.split(',')
      for c in codes:
        if len(c) > 2 and int(c[0:2]) in constructer_codes_:
          if print_to_stdout:
            print ','.join((id, name))
          else:
            constructer_funders_.add(id)
            constructer_fundings_[id] = 0

def aggregate_incomes(work_dir, print_tax_id_only):
  csv_files = glob.glob(os.path.join(work_dir, '*', 'incomes.csv'))
  # process header
  header = ['candidate', 'election', 'serail', 'transaction_date', 'account',
            'funder', 'founder_id', 'amount', 'is_cash', 'address', 'phone',
            'region', 'year']
  # trim 序號, 支出金額, 支出用途, 資料更正日期
  discard_indexes = [0, 9, 10, 14]
  discard_indexes.reverse()
  # process incomes.csv
  for fname in csv_files:
    # expect archive folder name to be 'xxx-xxx-{3digits year}xxx-{region}',
    # e.g. election-108080203-107105-10001
    archive = os.path.basename(os.path.dirname(fname))
    _, _, year, region = archive.split('-')
    year = year[:3]
    with open(fname) as csv:
      # skip original header
      csv.readline()
      for line in csv:
        cols = line.rstrip().split(',')
        # discard unused fields
        for d in discard_indexes:
          del cols[d]
        # naive cleanup
        for i in xrange(len(cols)):
          cols[i] = cols[i].strip('"')
        funder_id = cols[header.index('founder_id')]
        account_idx = header.index('account')
        if not print_tax_id_only:
          # distinguish constructer biz from others thru `accout`
          if funder_id in constructer_funders_:
            cols[account_idx] = '營造業捐贈收入'
            constructer_fundings_[funder_id] += float(cols[header.index('amount')])
          print '{},{},{}'.format(','.join(cols), region_code_[region], year)
        else:
          if funder_id.isdigit():
            print founder_id

def pivot_accounts(csv_file):
  with open(csv_file) as f:
    f.readline()
    header = ('region',) + account_categories_
    print ','.join(header)
    # init
    reset_values = lambda : ['0'] * len(account_categories_)
    region = ''
    values = reset_values()
    for line in f:
      next_region, account, amount = line.rstrip().split(',')
      if next_region != region:
        if region:
          print '{},{}'.format(region, ','.join(values))
        region = next_region
        values = reset_values()
      values[account_categories_.index(account)] = str(amount)
    # last record
    if region:
        print '{},{}'.format(region, ','.join(values))


def preprocess_election_report(election_report):
  with open(election_report) as f:
    print f.readline().rstrip()
    last_region = ''
    to_uni = lambda x : x.decode('utf-8')
    for line in f:
      cols = line.rstrip().split(',')
      if cols[0]:
        last_region = cols[0]
      else:
        cols[0] = last_region
      # remove '縣/市' if possible
      ambiguous = map(to_uni, ['新竹', '嘉義'])
      uni_name = cols[0].decode('utf-8')[0:3]
      if uni_name[0:2] not in ambiguous:
        uni_name = uni_name[0:2]
      cols[0] = uni_name.encode('utf-8')
      print ','.join(cols)


def main():
  args = getArgs()

  if args.funder_csv is not None:
    populate_constructer_info(args.funder_csv, args.list_constructers)
    if args.list_constructers:
      return

  if args.dir is not None:
    aggregate_incomes(args.dir, args.tax_id)
    return

  if args.pivot_accounts is not None:
    pivot_accounts(args.pivot_accounts)
    return

  if args.preprocess_election_report is not None:
    preprocess_election_report(args.preprocess_election_report)

if __name__ == '__main__':
  main()
