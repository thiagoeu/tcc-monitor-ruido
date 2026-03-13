# Sistema de Monitoramento Acústico IoT

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-B+-c51a4a?logo=raspberry-pi)](https://www.raspberrypi.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-black?logo=flask)](https://flask.palletsprojects.com/)

**Solução de monitoramento acústico distribuído baseada em IoT para mapeamento e controle de níveis sonoros em tempo real.**

[Funcionalidades](#funcionalidades) •
[Arquitetura](#arquitetura) •
[Hardware](#hardware) •
[Instalação](#instalação) •
[API](#api) •
[Contribuição](#contribuição)

</div>

## 📋 Sobre o Projeto

Este projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC) em Engenharia de Computação no Instituto Federal da Paraíba (IFPB) - Campus Campina Grande. O sistema permite o monitoramento acústico contínuo de ambientes utilizando sensores conectados a uma Raspberry Pi, com visualização em tempo real e geração de relatórios históricos.

### Autores

- Daniel Barbosa Vasconcelos
- Thiago Barbosa de Araujo
- Victor José Cordeiro de Medeiros

## ✨ Funcionalidades

### Monitoramento em Tempo Real

- Coleta de dados de pressão sonora a cada 5 segundos
- Visualização gráfica dos níveis de ruído por ambiente
- Dashboard interativo com atualização automática

### Gestão de Ambientes e Sensores

- Cadastro, edição e exclusão de ambientes monitorados
- Configuração personalizada de limites por ambiente/sensor
- Mapeamento visual dos pontos de monitoramento

### Sistema de Alertas

- Notificações automáticas quando limites são ultrapassados
- Alertas visuais no dashboard e no hardware (LEDs/LCD)
- Registro histórico de violações

### Relatórios e Análises

- Geração de relatórios em PDF com filtros personalizados
- Exportação de dados históricos
- Análise de conformidade com padrões de ruído

## 🏗️ Arquitetura

O sistema segue uma arquitetura distribuída com processamento local:
