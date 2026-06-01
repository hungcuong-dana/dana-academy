#include <bits/stdc++.h>
using namespace std;
int main(){
    freopen("TANSO.INP","r",stdin); freopen("TANSO.OUT","w",stdout);
    string s; getline(cin,s);
    while(!s.empty()&&(s.back()=='\r'||s.back()=='\n'||s.back()==' ')) s.pop_back();
    int n=s.size(), best=0;
    for(int i=0;i<n;i++){ int cnt[26]={0}, mx=0;
        for(int j=i;j<n;j++){ int v=++cnt[s[j]-'a']; if(v>mx)mx=v;
            if(mx*2>(j-i+1) && j-i+1>best) best=j-i+1; } }
    printf("%d\n",best); return 0;
}
