# -*- coding: utf-8 -*-

from ccxt.base.exchange import Exchange
from ccxt.base.errors import ExchangeError


class cryptocompare(Exchange):

    def describe(self):
        return self.deep_extend(super(cryptocompare, self).describe(), {
            'id': 'cryptocompare',
            'name': 'CryptoCompare',
            'rateLimit': 6000,
            'countries': 'UK',
            'hasCORS': False,
            'hasPrivateAPI': False,
            'hasCreateOrder': False,
            'hasCancelOrder': False,
            'hasFetchBalance': False,
            'hasFetchOrderBook': False,
            'hasFetchTrades': False,
            'hasFetchTickers': True,
            'hasFetchOHLCV': True,
            'timeframes': {
                '1m': {'timeframe': '1m', 'aggregate': 1},
                '5m': {'timeframe': '1m', 'aggregate': 5},
                '15m': {'timeframe': '1m', 'aggregate': 15},
                '30m': {'timeframe': '1m', 'aggregate': 30},
                '1h': {'timeframe': '1h', 'aggregate': 1},
                '2h': {'timeframe': '1h', 'aggregate': 2},
                '4h': {'timeframe': '1h', 'aggregate': 4},
                '12h': {'timeframe': '1h', 'aggregate': 12},
                '1d': {'timeframe': '1d', 'aggregate': 1},
                '1w': {'timeframe': '1d', 'aggregate': 7},
                '2w': {'timeframe': '1d', 'aggregate': 14},
                '1M': {'timeframe': '1d', 'aggregate': 30}
            },
            'urls': {
                'logo': 'https://www.cryptocompare.com/media/19990/logo-bold.svg',
                'api': 'https://min-api.cryptocompare.com/data',
                'www': 'https://www.cryptocompare.com',
                'doc': 'https://www.cryptocompare.com/api',
            },
            'api': {
                'public': {
                    'get': [
                        'all/coinlist',
                        'price',
                        'pricemulti',
                        'pricemultifull',
                        'generateAvg',
                        'dayAvg',
                        'pricehistorical',
                        'coinsnapshot',
                        'coinsnapshotfullbyid',
                        'socialstats',
                        'histominute',
                        'histohour',
                        'histoday',
                        'miningequipment',
                        'top/pairs',
                     ],
                },
            },
            'currencies': [
                'AUD',
                'BRL',
                'CAD',
                'CHF',
                'CNY',
                'EUR',
                'GBP',
                'HKD',
                'IDR',
                'INR',
                'JPY',
                'KRW',
                'MXN',
                'RUB',
                'USD',
                ],
        })

    def fetch_markets(self):
        response = self.publicGetAllCoinlist()
        markets = response['Data']
        keys = list(markets.keys())
        result = []
        for p in range(0, len(keys)):
            key = keys[p]
            for c in range(0, len(self.currencies)):
                market = markets[key]
                base = key
                baseId = key.upper()
                quote = self.currencies[c]
                quoteId = quote.upper()
                symbol = base + '/' + quote
                id = baseId + quoteId
                result.append({
                        'id': id,
                        'symbol': symbol,
                        'base': base,
                        'baseId': baseId,
                        'quote': quote,
                        'quoteId': quoteId,
                        'info': market,
                })
        return result

    def parse_ticker(self, ticker, market):
        timestamp = self.milliseconds()
        if 'LASTUPDATE' in ticker:
            if ticker['LASTUPDATE']:
                timestamp = int(ticker['LASTUPDATE']) * 1000
        baseVolumeKey = 'VOLUME24HOUR'
        baseVolume = None
        if baseVolumeKey in ticker:
            baseVolume = float(ticker[baseVolumeKey])
        quoteVolumeKey = 'VOLUME24HOURTO'
        quoteVolume = None
        if quoteVolumeKey in ticker:
            quoteVolume = float(ticker[quoteVolumeKey])
        change = None
        changeKey = 'CHANGEPCT24HOUR'
        if changeKey in ticker:
            change = float(ticker[changeKey])
        priceKey = 'PRICE'
        last = None
        if priceKey in ticker:
            if ticker[priceKey]:
                last = float(ticker[priceKey])
        open = None
        openKey = 'OPENDAY'
        if openKey in ticker:
            open = float(ticker[openKey])
        high = None
        highKey = 'HIGH24HOUR'
        if highKey in ticker:
            high = float(ticker[highKey])
        low = None
        lowKey = 'LOW24HOUR'
        if lowKey in ticker:
            low = float(ticker[lowKey])
        symbol = market['symbol']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': high,
            'low': low,
            'bid': None,
            'ask': None,
            'vwap': None,
            'open': open,
            'close': None,
            'first': None,
            'last': last,
            'change': change,
            'percentage': None,
            'average': None,
            'baseVolume': baseVolume,
            'quoteVolume': quoteVolume,
            'info': ticker,
        }

    def fetch_ticker(self, symbol, params):
        self.load_markets()
        market = self.market(symbol)
        request = self.extend({'fsyms': market['baseId'],
                               'tsyms': market['quoteId']}, params)
        response = self.publicGetPricemultifull(request)
        ticker = response['RAW'][market['baseId']][market['quoteId']]
        return self.parse_ticker(ticker, market)

    def parse_ohlcv(self, ohlcv, market, timeframe, since, limit):
        return [
         ohlcv['time'] * 1000,
         float(ohlcv['open']),
         float(ohlcv['high']),
         float(ohlcv['low']),
         float(ohlcv['close']),
         float(ohlcv['volumeto'])]

    def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        self.load_markets()
        market = self.market(symbol)
        request = self.extend({'fsym': market['baseId'],
                               'tsym': market['quoteId'],
                               'e': 'CCCAGG'}, params)
        if limit:
            request['limit'] = limit
        else:
            request['allData'] = True
        period = self.timeframes[timeframe]
        if period['timeframe'] is '1m':
            response = self.publicGetHistominute(self.extend(
                    request, params,
                    {'aggregate': self.timeframes[timeframe]['aggregate']}))
        else:
            if period['timeframe'] is '1h':
                response = self.publicGetHistohour(self.extend(
                        request, params,
                        {'aggregate':
                            self.timeframes[timeframe]['aggregate']}))
            elif period['timeframe'] is '1d':
                response = self.publicGetHistoday(self.extend(
                        request, params,
                        {'aggregate':
                            self.timeframes[timeframe]['aggregate']}))
            ohlcvs = response['Data']
        return self.parse_ohlcvs(ohlcvs, market, timeframe, since, limit)

    def sign(self, path, api='public', method='GET',
             params={}, headers=None, body=None):
        url = self.urls['api'] + '/' + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        if query:
            url += '?' + self.urlencode(query)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def request(self, path, api='public', method='GET',
                params={}, headers=None, body=None):
        response = self.fetch2(path, api, method, params, headers, body)
        return response
