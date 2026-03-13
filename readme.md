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

  <table>
  <tr>
    <td align="center">
      <a href="https://github.com/thiagoeu" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/95484968?v=4" width="100px;" alt="Avatar Victor"/><br>
        <sub>
          <b>Thiago Barbosa de Araujo</b>
        </sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Dcorder123" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/101361658?v=4" width="100px;" alt="Avatar Daniel"/><br>
        <sub>
          <b>Daniel Barbosa Vasconcelos</b>
        </sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/victorjcm" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/79644504?v=4" width="100px;" alt="Avatar Victor"/><br>
        <sub>
          <b>Victor José de Medeiros</b>
        </sub>
      </a>
    </td>
  </tr>
</table>

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

### Componentes Principais

1. **Camada de Coleta**: Sensores E06A com comunicação RS485
2. **Camada de Processamento**: Raspberry Pi B+ com backend Flask
3. **Camada de Armazenamento**: Banco de dados SQLite local
4. **Camada de Apresentação**: Dashboard web responsivo

## 🔧 Hardware

### Lista de Materiais (BoM)

| Item                 | Quantidade | Descrição                        | Custo Estimado (R$) |
| -------------------- | ---------- | -------------------------------- | ------------------- |
| Raspberry Pi B+      | 1          | Servidor central e processamento | 400,00              |
| Conversor USB-RS485  | 1          | Interface de comunicação         | 29,00               |
| Sensor E06A          | 1+         | Coleta de dados acústicos        | -                   |
| Cartão MicroSD 16GB  | 1          | Armazenamento                    | 15,00               |
| Protoboard e jumpers | 1          | Montagem e conexões              | 10,00               |
| Caixa impressa 3D    | 1          | Estrutura física                 | 7,00                |
| **Total Estimado**   |            |                                  | **537,00**          |

### Especificações Técnicas

- **Sensor**: E06A com interface RS485
- **Processador**: Raspberry Pi B+ (512MB RAM)
- **Comunicação**: RS485 para coleta, Wi-Fi/Ethernet para web
- **Armazenamento**: SQLite em cartão SD

## 💻 Software

### Stack Tecnológica

#### Backend

- **Framework**: Flask (Python 3.9+)
- **Banco de Dados**: SQLite + SQLAlchemy ORM
- **Comunicação Serial**: PySerial para leitura dos sensores

#### Frontend

### Backend

#### Infraestrutura

- **Container**: Docker (opcional)
- **CI/CD**: GitHub Actions
- **Monitoramento**: Prometheus + Grafana (planejado)

## 📦 Instalação

### Pré-requisitos

- Raspberry Pi B+ com Raspbian OS
- Python 3.9+
- Git
