#include <bits/stdc++.h>
using namespace std;
int main(){
    freopen("TANSO.INP","r",stdin);
    freopen("TANSO.OUT","w",stdout);
    string s; getline(cin,s);
    while(!s.empty() && (s.back()=='\r'||s.back()=='\n'||s.back()==' ')) s.pop_back();
    int n=s.size();
    int best=0;
    vector<int> pre(n+1), stk;
    for(int ci=0; ci<26; ci++){
        char c='a'+ci;
        if(s.find(c)==string::npos) continue;
        pre[0]=0;
        for(int i=0;i<n;i++) pre[i+1]=pre[i]+(s[i]==c?1:-1);
        stk.clear();
        for(int i=0;i<=n;i++) if(stk.empty()||pre[stk.back()]>pre[i]) stk.push_back(i);
        for(int j=n;j>=0;j--)
            while(!stk.empty() && pre[stk.back()]<pre[j]){
                if(j-stk.back()>best) best=j-stk.back();
                stk.pop_back();
            }
    }
    printf("%d\n", best);
    return 0;
}
