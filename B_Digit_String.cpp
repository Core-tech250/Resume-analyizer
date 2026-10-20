#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        string s;
        cin >> s;
        int n = s.length();                 

        s.erase(remove(s.begin(), s.end(), '4'), s.end());   

        int total13 = 0;                   
        for (char c : s) {
            if (c == '1' || c == '3') total13++;
        }

        int c2 = 0;                        
        int p13 = 0;                       
        int best = total13;                 

        for (char c : s) {
            if (c == '2') c2++;
            else p13++;                    

            best = max(best, c2 + (total13 - p13));
        }

        cout << n - best << "\n";
    }
    return 0;
}