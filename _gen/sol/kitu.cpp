#include <bits/stdc++.h>
using namespace std;
int main(){
    freopen("KITU.INP","r",stdin);
    freopen("KITU.OUT","w",stdout);
    long long n,k;
    if(scanf("%lld %lld",&n,&k)!=2) return 0;
    long long cnt[26]={0};
    int c;
    while((c=getchar())!=EOF) if(c>='A'&&c<='Z') cnt[c-'A']++;
    string res;
    for(int i=0;i<26;i++) if(cnt[i]>=k) res.push_back('A'+i);
    printf("%s\n", res.empty() ? "0" : res.c_str());
    return 0;
}
