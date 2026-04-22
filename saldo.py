#!/usr/bin/env python3
"""
PEGASUS WALLET BALANCE CHECKER - COMPLETE EDITION
Mengecek semua saldo BTC dari file JSON dan menampilkan wallet dengan saldo
"""

import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import sys
from colorama import init, Fore, Back, Style
import pandas as pd
from tabulate import tabulate

# Inisialisasi colorama untuk Windows
init()

class PegasusBalanceChecker:
    def __init__(self):
        self.results = []
        self.wallets_with_balance = []
        self.total_btc_found = 0
        self.api_url = "https://blockchain.info/balance?active="
        self.api_backup = "https://blockstream.info/api/address/"
        self.api_blockchair = "https://api.blockchair.com/bitcoin/dashboards/address/"
        
    def print_banner(self):
        """Tampilkan banner"""
        banner = f"""
{Fore.CYAN}{'='*60}
{Fore.YELLOW}   ╔═══════════════════════════════════════════════╗
   ║     PEGASUS WALLET BALANCE CHECKER v2.0      ║
   ║        Complete BTC Balance Scanner           ║
   ╚═══════════════════════════════════════════════╝
{Fore.CYAN}{'='*60}{Style.RESET_ALL}
"""
        print(banner)
    
    def load_wallet_file(self, file_path):
        """Load wallet data dari file JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            wallets = []
            
            # Deteksi berbagai format file
            if isinstance(data, dict):
                if 'keys' in data:
                    wallets = data['keys']
                elif 'wallets' in data:
                    wallets = data['wallets']
                elif 'addresses' in data:
                    wallets = data['addresses']
                elif 'result' in data and isinstance(data['result'], list):
                    wallets = data['result']
                else:
                    # Coba cari array dalam dict
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            if any(isinstance(item, dict) for item in value):
                                wallets = value
                                break
                    if not wallets:
                        wallets = [data]
            elif isinstance(data, list):
                wallets = data
            else:
                wallets = []
            
            # Validasi dan bersihkan data
            valid_wallets = []
            for w in wallets:
                if isinstance(w, dict):
                    # Ekstrak informasi yang diperlukan
                    address = w.get('address') or w.get('addr') or w.get('bitcoin_address') or w.get('id')
                    if address:
                        valid_wallets.append({
                            'address': address,
                            'private_key_wif': w.get('private_key_wif') or w.get('wif') or w.get('private_key'),
                            'private_key_hex': w.get('private_key_hex') or w.get('hex') or w.get('privkey'),
                            'source_index': len(valid_wallets)
                        })
            
            return valid_wallets
            
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Gagal membaca file: {e}{Style.RESET_ALL}")
            return None
    
    def check_balance_multiple_apis(self, address):
        """Cek saldo menggunakan multiple API untuk akurasi"""
        
        # API 1: Blockchain.info
        try:
            response = requests.get(f"{self.api_url}{address}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if address in data:
                    balance = data[address]['final_balance'] / 1e8
                    return {
                        'balance': balance,
                        'source': 'blockchain.info',
                        'success': True
                    }
        except:
            pass
        
        time.sleep(0.5)
        
        # API 2: Blockstream
        try:
            response = requests.get(f"{self.api_backup}{address}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                chain_stats = data.get('chain_stats', {})
                funded = chain_stats.get('funded_txo_sum', 0)
                spent = chain_stats.get('spent_txo_sum', 0)
                balance = (funded - spent) / 1e8
                return {
                    'balance': balance,
                    'source': 'blockstream.info',
                    'success': True
                }
        except:
            pass
        
        time.sleep(0.5)
        
        # API 3: Blockchair
        try:
            response = requests.get(f"{self.api_blockchair}{address}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and address in data['data']:
                    balance = data['data'][address]['address']['balance'] / 1e8
                    return {
                        'balance': balance,
                        'source': 'blockchair.com',
                        'success': True
                    }
        except:
            pass
        
        return {'balance': 0, 'source': 'none', 'success': False}
    
    def check_wallet_balance(self, wallet):
        """Cek saldo untuk satu wallet"""
        address = wallet.get('address')
        if not address:
            return None
        
        # Tampilkan progress
        sys.stdout.write(f"\r{Fore.CYAN}[SCAN] Checking: {address[:10]}...{Style.RESET_ALL}")
        sys.stdout.flush()
        
        # Cek saldo
        result = self.check_balance_multiple_apis(address)
        
        wallet_data = {
            'address': address,
            'balance_btc': result['balance'],
            'private_key_wif': wallet.get('private_key_wif'),
            'private_key_hex': wallet.get('private_key_hex'),
            'api_source': result['source'],
            'checked_at': datetime.now().isoformat(),
            'has_balance': result['balance'] > 0
        }
        
        return wallet_data
    
    def scan_all_wallets(self, wallets, max_workers=5):
        """Scan semua wallet"""
        if not wallets:
            print(f"{Fore.RED}[ERROR] Tidak ada wallet untuk discan{Style.RESET_ALL}")
            return []
        
        print(f"\n{Fore.GREEN}[INFO] Memulai scan {len(wallets)} wallet...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[INFO] Menggunakan {max_workers} thread parallel{Style.RESET_ALL}")
        print("-" * 60)
        
        self.results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_wallet = {
                executor.submit(self.check_wallet_balance, wallet): wallet 
                for wallet in wallets
            }
            
            completed = 0
            for future in as_completed(future_to_wallet):
                result = future.result()
                if result:
                    self.results.append(result)
                    completed += 1
                    
                    # Tampilkan progress
                    progress = (completed / len(wallets)) * 100
                    sys.stdout.write(f"\r{Fore.CYAN}[PROGRESS] {completed}/{len(wallets)} ({progress:.1f}%) - Found: {len([r for r in self.results if r['has_balance']])} wallets with balance{Style.RESET_ALL}")
                    sys.stdout.flush()
                    
                    # Jika ditemukan saldo, tampilkan langsung
                    if result['has_balance']:
                        print(f"\n{Fore.GREEN}{'!'*60}")
                        print(f"[FOUND] SALDO DITEMUKAN!")
                        print(f"Address: {result['address']}")
                        print(f"Balance: {result['balance_btc']:.8f} BTC")
                        print(f"Source : {result['api_source']}")
                        if result['private_key_wif']:
                            print(f"WIF Key: {result['private_key_wif']}")
                        print(f"{'!'*60}{Style.RESET_ALL}\n")
                
                time.sleep(0.2)  # Hindari rate limiting
        
        elapsed = time.time() - start_time
        print(f"\n\n{Fore.GREEN}[INFO] Scan selesai dalam {elapsed:.2f} detik{Style.RESET_ALL}")
        
        # Filter wallet dengan saldo
        self.wallets_with_balance = [r for r in self.results if r['has_balance']]
        self.total_btc_found = sum(r['balance_btc'] for r in self.wallets_with_balance)
        
        return self.results
    
    def display_rich_summary(self):
        """Tampilkan ringkasan lengkap dengan tabel"""
        if not self.results:
            print(f"{Fore.RED}[ERROR] Tidak ada data untuk ditampilkan{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"📊 RINGKASAN SCAN WALLET")
        print(f"{'='*80}{Style.RESET_ALL}")
        
        # Statistik umum
        total_wallets = len(self.results)
        active_wallets = len(self.wallets_with_balance)
        zero_wallets = total_wallets - active_wallets
        btc_price_usd = 60000  # Harga estimasi
        
        print(f"\n{Fore.YELLOW}📈 STATISTIK UMUM:{Style.RESET_ALL}")
        print(f"   Total wallet discan    : {Fore.WHITE}{total_wallets:,}{Style.RESET_ALL}")
        print(f"   Wallet dengan saldo    : {Fore.GREEN if active_wallets > 0 else Fore.RED}{active_wallets:,}{Style.RESET_ALL}")
        print(f"   Wallet kosong          : {zero_wallets:,}")
        print(f"   Total BTC ditemukan    : {Fore.GREEN}{self.total_btc_found:.8f} BTC{Style.RESET_ALL}")
        print(f"   Nilai dalam USD        : {Fore.GREEN}${self.total_btc_found * btc_price_usd:,.2f}{Style.RESET_ALL}")
        
        if active_wallets > 0:
            # Tabel wallet dengan saldo
            print(f"\n{Fore.YELLOW}💰 WALLET DENGAN SALDO:{Style.RESET_ALL}")
            
            table_data = []
            for i, wallet in enumerate(sorted(self.wallets_with_balance, key=lambda x: x['balance_btc'], reverse=True), 1):
                wif_short = wallet['private_key_wif'][:15] + "..." if wallet['private_key_wif'] and len(wallet['private_key_wif']) > 15 else wallet['private_key_wif']
                table_data.append([
                    i,
                    wallet['address'][:15] + "..." if len(wallet['address']) > 15 else wallet['address'],
                    f"{wallet['balance_btc']:.8f}",
                    f"${wallet['balance_btc'] * btc_price_usd:,.2f}",
                    wif_short or "N/A",
                    wallet['api_source']
                ])
            
            headers = ['No', 'Address', 'Balance (BTC)', 'Value (USD)', 'WIF Key', 'Source']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
            
            # Detail lengkap wallet dengan saldo
            print(f"\n{Fore.YELLOW}🔑 DETAIL LENGKAP WALLET DENGAN SALDO:{Style.RESET_ALL}")
            print("=" * 80)
            
            for i, wallet in enumerate(sorted(self.wallets_with_balance, key=lambda x: x['balance_btc'], reverse=True), 1):
                print(f"\n{Fore.GREEN}WALLET #{i}{Style.RESET_ALL}")
                print(f"   Address       : {wallet['address']}")
                print(f"   Balance       : {Fore.GREEN}{wallet['balance_btc']:.8f} BTC (${wallet['balance_btc'] * btc_price_usd:,.2f}){Style.RESET_ALL}")
                if wallet['private_key_wif']:
                    print(f"   WIF Private Key: {Fore.YELLOW}{wallet['private_key_wif']}{Style.RESET_ALL}")
                if wallet['private_key_hex']:
                    print(f"   HEX Private Key: {wallet['private_key_hex']}")
                print(f"   API Source    : {wallet['api_source']}")
                print(f"   Scan Time     : {wallet['checked_at']}")
                print("-" * 60)
        else:
            print(f"\n{Fore.RED}❌ TIDAK DITEMUKAN WALLET DENGAN SALDO{Style.RESET_ALL}")
    
    def save_complete_report(self, input_file):
        """Simpan laporan lengkap dalam berbagai format"""
        if not self.results:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        btc_price_usd = 60000
        
        # 1. JSON Format (Pegasus + Manukla)
        json_data = {
            "pegasus": {
                "version": "2.0.0",
                "scan_time": datetime.now().isoformat(),
                "source_file": input_file,
                "total_scanned": len(self.results),
                "wallets_with_balance": len(self.wallets_with_balance),
                "total_btc_found": round(self.total_btc_found, 8),
                "total_usd_value": round(self.total_btc_found * btc_price_usd, 2),
                "statistics": {
                    "total_wallets": len(self.results),
                    "active_wallets": len(self.wallets_with_balance),
                    "inactive_wallets": len(self.results) - len(self.wallets_with_balance),
                    "scan_duration_seconds": time.time() - start_time if 'start_time' in globals() else 0
                }
            },
            "wallets": self.results,
            "manukla": {
                "metadata": {
                    "source": input_file,
                    "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "apis_used": ["blockchain.info", "blockstream.info", "blockchair.com"]
                },
                "summary": {
                    "total_addresses": len(self.results),
                    "active_addresses": len(self.wallets_with_balance),
                    "total_balance": self.total_btc_found,
                    "richest_address": max(self.wallets_with_balance, key=lambda x: x['balance_btc'])['address'] if self.wallets_with_balance else None,
                    "richest_balance": max(self.wallets_with_balance, key=lambda x: x['balance_btc'])['balance_btc'] if self.wallets_with_balance else 0
                }
            }
        }
        
        json_file = f"pegasus_complete_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # 2. CSV Format untuk Excel
        if self.wallets_with_balance:
            csv_file = f"wallets_with_balance_{timestamp}.csv"
            df = pd.DataFrame(self.wallets_with_balance)
            df['value_usd'] = df['balance_btc'] * btc_price_usd
            df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # 3. Text Report
        txt_file = f"pegasus_report_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PEGASUS WALLET BALANCE REPORT - COMPLETE\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Scan Time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source File  : {input_file}\n")
            f.write(f"Total Wallets: {len(self.results)}\n\n")
            
            f.write("STATISTIK:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Wallet dengan saldo: {len(self.wallets_with_balance)}\n")
            f.write(f"Wallet kosong      : {len(self.results) - len(self.wallets_with_balance)}\n")
            f.write(f"Total BTC ditemukan: {self.total_btc_found:.8f}\n")
            f.write(f"Nilai USD estimasi : ${self.total_btc_found * btc_price_usd:,.2f}\n\n")
            
            if self.wallets_with_balance:
                f.write("=" * 80 + "\n")
                f.write("DAFTAR WALLET DENGAN SALDO\n")
                f.write("=" * 80 + "\n")
                
                for i, w in enumerate(sorted(self.wallets_with_balance, key=lambda x: x['balance_btc'], reverse=True), 1):
                    f.write(f"\n{i}. ADDRESS : {w['address']}\n")
                    f.write(f"   BALANCE  : {w['balance_btc']:.8f} BTC\n")
                    f.write(f"   VALUE USD: ${w['balance_btc'] * btc_price_usd:,.2f}\n")
                    if w['private_key_wif']:
                        f.write(f"   WIF KEY  : {w['private_key_wif']}\n")
                    if w['private_key_hex']:
                        f.write(f"   HEX KEY  : {w['private_key_hex']}\n")
                    f.write(f"   API SOURCE: {w['api_source']}\n")
                    f.write("-" * 60 + "\n")
            else:
                f.write("\nTIDAK ADA WALLET DENGAN SALDO!\n")
        
        print(f"\n{Fore.GREEN}✅ Laporan lengkap disimpan:{Style.RESET_ALL}")
        print(f"   📁 JSON: {json_file}")
        print(f"   📁 TXT : {txt_file}")
        if self.wallets_with_balance:
            print(f"   📁 CSV : {csv_file}")

def main():
    checker = PegasusBalanceChecker()
    checker.print_banner()
    
    while True:
        # Cari file JSON
        json_files = [f for f in os.listdir('.') if f.endswith('.json')]
        
        if json_files:
            print(f"{Fore.CYAN}File JSON ditemukan:{Style.RESET_ALL}")
            for i, file in enumerate(json_files, 1):
                size = os.path.getsize(file)
                print(f"   {i}. {file} ({size:,} bytes)")
            
            print(f"\nPilihan:")
            print(f"   1-{len(json_files)}: Pilih file")
            print(f"   m: Masukkan path manual")
            print(f"   q: Keluar")
            
            choice = input(f"\n{Fore.GREEN}Pilih: {Style.RESET_ALL}").strip()
            
            if choice.lower() == 'q':
                print(f"\n{Fore.YELLOW}Terima kasih telah menggunakan Pegasus Checker!{Style.RESET_ALL}")
                break
            elif choice.lower() == 'm':
                file_path = input("Masukkan path file: ").strip()
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(json_files):
                        file_path = json_files[idx]
                    else:
                        print(f"{Fore.RED}Pilihan tidak valid!{Style.RESET_ALL}")
                        continue
                except ValueError:
                    print(f"{Fore.RED}Input tidak valid!{Style.RESET_ALL}")
                    continue
        else:
            print(f"{Fore.YELLOW}Tidak ada file JSON di direktori ini{Style.RESET_ALL}")
            file_path = input("Masukkan path file manual (atau 'q' untuk keluar): ").strip()
            if file_path.lower() == 'q':
                break
        
        # Load wallet
        print(f"\n{Fore.CYAN}Membaca file: {file_path}{Style.RESET_ALL}")
        wallets = checker.load_wallet_file(file_path)
        
        if not wallets:
            print(f"{Fore.RED}Gagal membaca file atau tidak ada wallet valid{Style.RESET_ALL}")
            continue
        
        print(f"{Fore.GREEN}Ditemukan {len(wallets)} wallet valid{Style.RESET_ALL}")
        
        # Preview
        print(f"\n{Fore.CYAN}Preview 5 wallet pertama:{Style.RESET_ALL}")
        for i, w in enumerate(wallets[:5], 1):
            print(f"   {i}. Address: {w['address']}")
            if w['private_key_wif']:
                print(f"      WIF: {w['private_key_wif'][:20]}...")
        
        # Konfirmasi
        confirm = input(f"\n{Fore.GREEN}Lanjutkan scan semua wallet? (y/n): {Style.RESET_ALL}").strip().lower()
        if confirm != 'y':
            continue
        
        # Mulai scan
        global start_time
        start_time = time.time()
        results = checker.scan_all_wallets(wallets, max_workers=5)
        
        if results:
            # Tampilkan ringkasan
            checker.display_rich_summary()
            
            # Simpan laporan
            checker.save_complete_report(file_path)
            
            # Tanya scan lagi
            again = input(f"\n{Fore.GREEN}Scan file lain? (y/n): {Style.RESET_ALL}").strip().lower()
            if again != 'y':
                print(f"\n{Fore.YELLOW}Terima kasih telah menggunakan Pegasus Checker!{Style.RESET_ALL}")
                break
        else:
            print(f"{Fore.RED}Tidak ada hasil scan{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        # Install dependencies jika perlu
        try:
            import colorama
            import pandas
            import tabulate
        except ImportError as e:
            print("Menginstall dependencies yang diperlukan...")
            os.system("pip install colorama pandas tabulate requests")
            print("Silakan jalankan ulang script")
            sys.exit(0)
        
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Program dihentikan oleh user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()