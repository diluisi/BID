# Projeto BID para elaboração de protótipo de visualização do congestionamento a partir dos dados do Waze

O objetivo geral da atividade é validar se os dados gerados pelo aplicativo de navegação colaborativa Waze são capazes de descrever o congestionamento para as cidades de  São Paulo, Montevidéu, Quito, Xalapa e para o distrito de Miraflores em Lima.

Aplicamos métodos de análise exploratória de dados e observamos a correlação entre a curva real de tráfego e a curva obtida pelos dados do aplicativo. Para a curva real utilizamos os dados de observação utilizados pela Companhia de Engenharia de Tráfego de São Paulo. A escolha é devido a maturidade do modelo de gestão de tráfego em São Paulo, a validação com analistas experientes que acompanham o indicador de lentidão, a disponibilidade de dados históricos para comparação, e a familiaridade com os dados do aplicativo Waze já em uso na Companhia em outros serviços de monitoramento. O método da CET é invariante quanto ao tipo de cidade, podendo ser aplicado ou utilizado como validação nas demais cidades de nosso estudo.

No caso dos dados serem minimamente satisfatórios em termos de qualidade e significativa representação da condição de tráfego, a etapa seguinte é o desenvolvimento de um protótipo para gestão de tráfego das cidades. O protótipo possui as seguintes premissas:

* Usabilidade e foco na experiência do usuário;
* Código aberto;
* Interface que proporcione o diagnóstico do tráfego utilizando os dados históricos e tempo real;
* Portável;
* Extensível;
* Adaptável;
* Simples execução e manutenção;
* Escalabilidade da monitoração;
* Baixo custo.

O protótipo não representa um produto final, pois dependerá da infra-estrutura que cada cidade disponibiliza em ambiente de produção e adaptações serão necessárias. Detalhamos as principais adaptações na documentação final.

O relatório [Congestionamento_v2.pdf](https://github.com/diluisi/BID/blob/main/Congestionamento_v2.pdf) contém os detalhes da análise e como executar os arquivos do protótipo.

Abaixo está a visão geral da arquitetura:

![image](https://user-images.githubusercontent.com/6492834/125698215-cc2f93e2-eb5b-41ad-8bb4-6500df0480d2.png)
