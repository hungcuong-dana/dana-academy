#include <bits/stdc++.h>
using namespace std;
int main(){
    freopen("DAOXAU.INP","r",stdin);
    freopen("DAOXAU.OUT","w",stdout);
    string s; getline(cin,s);
    while(!s.empty() && (s.back()=='\r'||s.back()=='\n')) s.pop_back();
    int n=s.size();
    int m; if(scanf("%d",&m)!=1) return 0;
    int half=n/2;
    vector<int> diff(half+2,0);
    for(int i=0;i<m;i++){
        long long k; scanf("%lld",&k);
        long long L=(long long)n+1-k;
        if(L<1) L=1;
        if(L<=half) diff[L]++;
    }
    int run=0;
    for(int i=1;i<=half;i++){
        run+=diff[i];
        if(run&1) swap(s[i-1], s[n-i]);
    }
    printf("%s\n", s.c_str());
    return 0;
}
