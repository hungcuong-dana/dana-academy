#include <bits/stdc++.h>
using namespace std;
int main(){
    freopen("DAOXAU.INP","r",stdin); freopen("DAOXAU.OUT","w",stdout);
    string s; getline(cin,s);
    while(!s.empty()&&(s.back()=='\r'||s.back()=='\n')) s.pop_back();
    int n=s.size(), m; scanf("%d",&m);
    for(int i=0;i<m;i++){ long long k; scanf("%lld",&k);
        int L=n-k, R=k-1; reverse(s.begin()+L, s.begin()+R+1); }
    printf("%s\n", s.c_str()); return 0;
}
